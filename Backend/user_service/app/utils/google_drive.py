"""Google Drive utility for file storage"""
import os
import io
import uuid
import re
from typing import Optional
from fastapi import UploadFile, HTTPException
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_PATH = 'token.json'


class GoogleDriveService:
    """Google Drive service for file operations"""
    
    def __init__(self, credentials_path: str, folder_id: str):
        self.credentials_path = credentials_path
        self.folder_id = folder_id
        self.service = None
    
    def _authenticate(self):
        """Authenticate and build Google Drive service"""
        if self.service is not None:
            return
        
        creds = None
        
        # Load existing token
        if os.path.exists(TOKEN_PATH):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            except Exception:
                creds = None
        
        # Refresh if expired
        # Note: Access tokens expire after ~1 hour (Google security requirement)
        # Refresh tokens can be long-lived if app is in production status
        # For testing apps, refresh tokens expire after 7 days
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed token back to file
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                # Refresh token may have expired or been revoked
                creds = None
        
        # Re-authenticate if needed
        if not creds or not creds.valid:
            if not os.path.exists(self.credentials_path):
                raise HTTPException(
                    status_code=500,
                    detail=f"Credentials file not found: {self.credentials_path}"
                )
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0, open_browser=False)
                if creds:
                    with open(TOKEN_PATH, 'w') as token:
                        token.write(creds.to_json())
            except Exception:
                raise HTTPException(
                    status_code=500,
                    detail="Authentication failed. Generate token.json using generate_token.py"
                )
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def upload_file(self, file: UploadFile, user_id: str) -> str:
        """Upload file to Google Drive and return gdrive:// URL"""
        self._authenticate()
        
        try:
            file_content = file.file.read()
            file.file.seek(0)
            
            file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
            filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}{file_extension}"
            
            uploaded_file = self.service.files().create(
                body={'name': filename, 'parents': [self.folder_id]},
                media_body=MediaIoBaseUpload(
                    io.BytesIO(file_content),
                    mimetype=file.content_type or 'image/jpeg',
                    resumable=True
                ),
                fields='id'
            ).execute()
            
            # Make file publicly viewable
            self.service.permissions().create(
                fileId=uploaded_file['id'],
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            
            return f"gdrive://{uploaded_file['id']}/{filename}"
            
        except HttpError as error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file: {str(error)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Upload error: {str(e)}"
            )
    
    def delete_file(self, file_url: str) -> bool:
        """Delete file from Google Drive"""
        self._authenticate()
        
        try:
            file_id = self._extract_file_id(file_url)
            if not file_id:
                return False
            
            self.service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as error:
            return error.resp.status == 404
        except Exception:
            return False
    
    def _extract_file_id(self, url: str) -> Optional[str]:
        """Extract file ID from Google Drive URL"""
        if url.startswith('gdrive://'):
            match = re.match(r'gdrive://([^/]+)', url)
            return match.group(1) if match else None
        
        # Standard Google Drive URL patterns
        patterns = [
            r'[?&]id=([^&]+)',  # ?id=... or &id=...
            r'/file/d/([^/]+)',  # /file/d/...
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_file_view_url(self, file_id: str) -> str:
        """Get direct view URL for a Google Drive file"""
        return f"https://drive.google.com/uc?export=view&id={file_id}"


def convert_gdrive_url_to_endpoint_url(gdrive_url: Optional[str], base_url: str) -> Optional[str]:
    """Convert gdrive:// URL to API endpoint URL"""
    if not gdrive_url or not gdrive_url.startswith('gdrive://'):
        return gdrive_url
    
    parts = gdrive_url.replace('gdrive://', '').split('/', 1)
    if len(parts) == 2:
        return f"{base_url.rstrip('/')}/users/avatar/{parts[1]}"
    
    return gdrive_url
