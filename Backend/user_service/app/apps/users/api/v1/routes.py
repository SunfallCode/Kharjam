"""User API routes"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, Response, BackgroundTasks
from typing import Optional
from sqlalchemy.orm import Session
import httpx
import io
import logging
from app.db import get_db, SessionLocal
from app.apps.users.models import User
from app.apps.users.schemas import UserOut, UserUpdate, ErrorResponse
from app.apps.auth.services import PendingUpdateService
from app.apps.users.services import UserService
from app.utils.validators import FIELD_VALIDATORS, normalize_phone_number
from app.core.dependencies import get_current_user, get_drive_service
from app.core.errors import UserError
from app.utils.google_drive import convert_gdrive_url_to_endpoint_url, GoogleDriveService
from app.utils.validators import validate_image_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


def _convert_user_avatar_url(user: User, request: Request) -> UserOut:
    """Convert user avatar URL from gdrive:// format to endpoint URL"""
    user_out = UserOut.model_validate(user)
    if user_out.avatar_url and user_out.avatar_url.startswith('gdrive://'):
        user_out.avatar_url = convert_gdrive_url_to_endpoint_url(
            user_out.avatar_url, str(request.base_url)
        )
    return user_out


def _handle_avatar_deletion(user: User, drive_service: GoogleDriveService):
    """Helper to delete avatar if exists"""
    if user.avatar_url:
        drive_service.delete_file(user.avatar_url)
        user.avatar_url = None


class SimpleUploadFile:
    """Simple UploadFile-like object for background tasks"""
    def __init__(self, file_content: bytes, filename: str, content_type: str):
        self.file = io.BytesIO(file_content)
        self.filename = filename
        self.content_type = content_type


def _upload_profile_image_background(
    file_content: bytes,
    filename: str,
    content_type: str,
    user_id: str,
    old_avatar_url: Optional[str]
):
    """Background task to upload profile image to Google Drive and update user"""
    db = SessionLocal()
    try:
        # Create drive service instance directly (not using dependency injection)
        from app.config.settings import google_drive_config
        drive_service = GoogleDriveService(
            credentials_path=google_drive_config.credentials_path,
            folder_id=google_drive_config.folder_id
        )
        
        # Delete old avatar if exists
        if old_avatar_url:
            try:
                drive_service.delete_file(old_avatar_url)
            except Exception as e:
                logger.warning(f"Failed to delete old avatar for user {user_id}: {str(e)}")
        
        # Create UploadFile-like object for the background task
        upload_file = SimpleUploadFile(file_content, filename, content_type)
        
        # Upload to Google Drive
        avatar_url = drive_service.upload_file(upload_file, user_id)
        
        # Update user's avatar_url in database
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.avatar_url = avatar_url
            db.commit()
            logger.info(f"Successfully uploaded profile image for user {user_id}")
        else:
            logger.error(f"User {user_id} not found when updating avatar_url")
            
    except Exception as e:
        logger.error(f"Failed to upload profile image for user {user_id}: {str(e)}", exc_info=True)
        db.rollback()
    finally:
        db.close()


@router.get(
    "/profile",
    response_model=UserOut,
    operation_id="getProfileApi",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or missing token"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> UserOut:
    """Get current user profile"""
    return _convert_user_avatar_url(current_user, request)


@router.patch(
    "/profile",
    response_model=UserOut,
    operation_id="updateProfileApi",
    responses={
        400: {"model": ErrorResponse, "description": "Bad request - Validation error or duplicate phone/email"},
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or missing token"},
        404: {"model": ErrorResponse, "description": "User not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_user_profile(
    request: Request,
    background_tasks: BackgroundTasks,
    name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    card_number: Optional[str] = Form(None),
    card_holder_name: Optional[str] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
    delete_profile_image: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    drive_service: GoogleDriveService = Depends(get_drive_service)
) -> UserOut:
    """Update user profile"""
    # Handle profile image upload (async background processing)
    if profile_image and profile_image.filename and profile_image.filename.strip():
        validate_image_file(profile_image)
        
        # Read file content synchronously before request completes
        file_content = await profile_image.read()
        filename = profile_image.filename
        content_type = profile_image.content_type or 'image/jpeg'
        old_avatar_url = current_user.avatar_url
        
        # Add background task to upload image
        background_tasks.add_task(
            _upload_profile_image_background,
            file_content,
            filename,
            content_type,
            current_user.id,
            old_avatar_url
        )
        
        # Note: avatar_url will be updated in background, user will see old avatar until upload completes
    
    # Handle profile image deletion
    elif delete_profile_image and delete_profile_image.lower() in ('true', '1', 'yes'):
        _handle_avatar_deletion(current_user, drive_service)
    
    # Handle email and phone number updates separately - they need OTP verification
    pending_updates = []

    if email is not None and email.strip():
        email_value = email.strip()
        # Validate email format
        email_validator = FIELD_VALIDATORS.get("email")
        if email_validator:
            email_validator(email_value)

        # Check uniqueness in database
        existing_user = db.query(User).filter(User.email == email_value, User.id != current_user.id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail=UserError.EMAIL_ALREADY_REGISTERED)

        # Cache email update only after validation
        result = PendingUpdateService.cache_pending_update(current_user.id, "email", email_value)
        if result["cached"]:
            pending_updates.append("email")
        else:
            logger.error(f"Failed to cache email update for user {current_user.id}")

    if phone_number is not None and phone_number.strip():
        phone_value = phone_number.strip()
        # Validate phone number format
        phone_validator = FIELD_VALIDATORS.get("phone_number")
        if phone_validator:
            phone_validator(phone_value)

        # Normalize phone number
        normalized_phone = normalize_phone_number(phone_value)

        # Check uniqueness in database
        existing_user = db.query(User).filter(
            User.phone_number == normalized_phone,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail=UserError.PHONE_ALREADY_REGISTERED)

        # Cache phone number update only after validation
        result = PendingUpdateService.cache_pending_update(current_user.id, "phone_number", normalized_phone)
        if result["cached"]:
            pending_updates.append("phone_number")
        else:
            logger.error(f"Failed to cache phone number update for user {current_user.id}")

    # Update other fields immediately (name, card details)
    immediate_update_fields = {
        'name': name,
        'card_number': card_number,
        'card_holder_name': card_holder_name
    }
    immediate_update_data = {k: v for k, v in immediate_update_fields.items() if v is not None}

    if immediate_update_data:
        UserService.validate_and_update_user(current_user, UserUpdate(**immediate_update_data), db)

    db.commit()
    db.refresh(current_user)

    # Create response
    response_data = _convert_user_avatar_url(current_user, request)

    # Add information about pending updates
    if pending_updates:
        response_data.pending_updates = pending_updates
        response_data.message = f"Profile updated. Pending verification for: {', '.join(pending_updates)}"

    return response_data


@router.get(
    "/avatar/{filename:path}",
    operation_id="getAvatarApi",
    include_in_schema=False,
    responses={
        404: {"model": ErrorResponse, "description": "Avatar not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_avatar(
    filename: str,
    db: Session = Depends(get_db),
    drive_service: GoogleDriveService = Depends(get_drive_service)
) -> Response:
    """Get avatar image from Google Drive"""
    # Find user with avatar_url containing this filename
    user = db.query(User).filter(User.avatar_url.like(f'%{filename}')).first()
    
    if not user or not user.avatar_url:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    file_id = drive_service._extract_file_id(user.avatar_url)
    if not file_id:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    # Fetch image from Google Drive
    view_url = drive_service.get_file_view_url(file_id)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(view_url, follow_redirects=True, timeout=30.0)
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Avatar not found")
            
            # Determine content type from filename extension
            content_type = "image/png" if filename.lower().endswith('.png') else "image/jpeg"
            
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{filename}"',
                    "Cache-Control": "public, max-age=31536000",
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch avatar: {str(e)}")

