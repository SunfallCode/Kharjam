"""Auth API routes"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from typing import Optional
from sqlalchemy.orm import Session
from app.db import get_db
from app.apps.auth.schemas import (
    RequestOTPRequest,
    RequestOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    UserData,
    TokenResponse,
    RefreshRequest,
    LogoutResponse,
    ErrorResponse,
)
from app.apps.auth.services import OTPService, JWTService, TokenBlacklistService, PendingUpdateService
from app.apps.auth.selectors import TokenSelector
from app.apps.users.models import User, UserRole
from app.apps.users.selectors import UserSelector
from app.utils.validators import normalize_phone_number
from app.utils.google_drive import convert_gdrive_url_to_endpoint_url
from app.core.dependencies import extract_token, get_current_user, get_current_user_optional
from app.core.errors import AuthError, UserError

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/request-otp",
    response_model=RequestOTPResponse,
    operation_id="requestOtpApi",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid token"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def request_otp(
    request: RequestOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Request OTP"""
    if request.purpose == "auth":
        # Original auth logic
        identifier_type = OTPService.get_identifier_type(request.identifier)
        user = UserSelector.get_by_identifier(db, request.identifier)

        if not user:
            # Create temporary user for OTP
            user_data = {
                "name": "",
                "role": UserRole.user
            }
            if identifier_type == "email":
                user_data["email"] = request.identifier
                user_data["phone_number"] = None
            else:
                user_data["phone_number"] = normalize_phone_number(request.identifier)
                user_data["email"] = None

            user = UserSelector.create(db, user_data)

        user_id = user.id
        send_identifier = request.identifier

    elif request.purpose == "update":
        # For updates, user must be authenticated
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required for profile updates")

        user_id = current_user.id
        user = current_user

        # Check for pending updates (auto-detect field)
        pending_updates = PendingUpdateService.get_all_pending_updates(user_id)
        if not pending_updates:
            raise HTTPException(status_code=400, detail="No pending updates found")

        # Use the first available pending update (prioritize email, then phone)
        if "email" in pending_updates:
            identifier_type = "email"
            pending_update = pending_updates["email"]
        elif "phone_number" in pending_updates:
            identifier_type = "phone_number"
            pending_update = pending_updates["phone_number"]
        else:
            raise HTTPException(status_code=400, detail="No valid pending updates found")

        send_identifier = pending_update["value"]

    else:
        raise HTTPException(status_code=400, detail="Invalid purpose")

    # Normalize phone number if needed
    if identifier_type == "phone_number":
        send_identifier = normalize_phone_number(send_identifier)

    # Create OTP with purpose (field auto-detected for updates)
    otp = OTPService.create_otp(user_id, request.purpose)

    # Send OTP message in background
    background_tasks.add_task(
        OTPService.send_otp_message,
        send_identifier,
        otp["code"],
        identifier_type
    )

    message = f"OTP generated successfully. Note: Message service is currently unavailable."

    return RequestOTPResponse(
        message=message,
        identifier_type=identifier_type,
        otp_code=otp["code"]
    )


@router.post(
    "/verify-otp",
    operation_id="verifyOtpApi",
    responses={
        400: {"model": ErrorResponse, "description": "Bad request - Invalid OTP or user not found"},
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid token"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def verify_otp(
    request: VerifyOTPRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Verify OTP and authenticate or apply pending updates"""
    identifier_type = OTPService.get_identifier_type(request.identifier)

    if request.purpose == "auth":
        # Original auth logic
        user = UserSelector.get_by_identifier(db, request.identifier)
        if not user:
            raise HTTPException(status_code=400, detail=UserError.OTP_NOT_REQUESTED)

        if not OTPService.validate_otp(user.id, request.otp_code, request.purpose):
            raise HTTPException(status_code=400, detail=UserError.INVALID_OTP)

        is_new_user = user.name == "" or user.name is None

        # Generate tokens
        access_token = JWTService.create_access_token({
            "user_id": user.id,
            "email": user.email,
            "phone_number": user.phone_number
        })
        refresh_token = JWTService.create_refresh_token({
            "user_id": user.id
        })

        # Get user name and avatar_url
        name = user.name if user.name and user.name.strip() else None
        avatar_url = user.avatar_url

        # Convert avatar_url if it's a gdrive:// URL
        if avatar_url:
            avatar_url = convert_gdrive_url_to_endpoint_url(avatar_url, str(http_request.base_url))

        # Create user_data object
        user_data = UserData(name=name, avatar_url=avatar_url)

        return VerifyOTPResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_data=user_data,
            is_new_user=is_new_user
        )

    elif request.purpose == "update":
        # For updates, user must be authenticated
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required for profile updates")

        user_id = current_user.id
        user = current_user

        # Validate OTP (auto-detects field)
        is_valid, identifier_type = OTPService.validate_otp(user_id, request.otp_code, request.purpose)
        if not is_valid:
            raise HTTPException(status_code=400, detail=UserError.INVALID_OTP)

        if not identifier_type:
            raise HTTPException(status_code=400, detail="No pending update found")

        # Get the pending update
        pending_update = PendingUpdateService.get_pending_update(user_id, identifier_type)
        if not pending_update:
            raise HTTPException(status_code=400, detail="No pending update found or update expired")

        # Apply the update
        update_value = pending_update["value"]
        if identifier_type == "phone_number":
            update_value = normalize_phone_number(update_value)

        # Check for uniqueness
        if identifier_type == "phone_number":
            existing_user = db.query(User).filter(
                User.phone_number == update_value,
                User.id != user.id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail=UserError.PHONE_ALREADY_REGISTERED)
        elif identifier_type == "email":
            existing_user = db.query(User).filter(
                User.email == update_value,
                User.id != user.id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail=UserError.EMAIL_ALREADY_REGISTERED)

        # Update the user
        setattr(user, identifier_type, update_value)
        db.commit()

        # Clear the pending update
        PendingUpdateService.clear_pending_update(user_id, identifier_type)

        # Return success response (no tokens for updates)
        return {
            "message": f"{identifier_type.replace('_', ' ').title()} updated successfully",
            "field": identifier_type,
            "value": update_value
        }

    else:
        raise HTTPException(status_code=400, detail="Invalid purpose")


@router.post(
    "/check-user",
    operation_id="checkUserApi",
    include_in_schema=False,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or blacklisted token"},
    },
)
def check_user(
    token: str = Depends(extract_token),
    db: Session = Depends(get_db)
):
    """Check if token is valid"""
    payload = JWTService.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail=AuthError.INVALID_TOKEN)

    if TokenSelector.is_blacklisted(db, token):
        raise HTTPException(status_code=401, detail=AuthError.TOKEN_BLACKLISTED)

    return {"msg": "Token is valid"}


@router.post(
    "/refresh",
    response_model=TokenResponse,
    operation_id="refreshTokenApi",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or blacklisted refresh token"},
        404: {"model": ErrorResponse, "description": "User not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token"""
    refresh_token = request.refresh_token

    payload = JWTService.decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail=AuthError.INVALID_REFRESH_TOKEN)

    # Check blacklist
    if TokenBlacklistService.is_blacklisted(refresh_token):
        raise HTTPException(status_code=401, detail=AuthError.TOKEN_BLACKLISTED)

    if TokenSelector.is_blacklisted(db, refresh_token):
        raise HTTPException(status_code=401, detail=AuthError.TOKEN_BLACKLISTED)

    user = UserSelector.get_by_id(db, payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail=UserError.NOT_FOUND)

    access_token = JWTService.create_access_token({
        "user_id": user.id,
        "email": user.email,
        "phone_number": user.phone_number
    })
    new_refresh_token = JWTService.create_refresh_token({"user_id": user.id})

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    operation_id="logoutApi",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid refresh token"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def logout(request: RefreshRequest, db: Session = Depends(get_db)):
    """Logout user"""
    refresh_token = request.refresh_token

    payload = JWTService.decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail=AuthError.INVALID_REFRESH_TOKEN)

    user_id = payload["user_id"]

    # Blacklist in database
    TokenSelector.blacklist(db, user_id, refresh_token)

    # Blacklist in Redis
    TokenBlacklistService.blacklist_token(refresh_token, expires_in=7*24*3600)

    return LogoutResponse(msg="Logged out successfully")

