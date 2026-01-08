#!/usr/bin/env python3
"""Generate Google Drive OAuth token.json

IMPORTANT NOTES ABOUT TOKEN EXPIRATION:
- Access tokens ALWAYS expire (~1 hour) - this is a Google security requirement
- Refresh tokens can be long-lived:
  * Testing apps: Refresh tokens expire after 7 days
  * Production apps: Refresh tokens can last indefinitely if used regularly
  * Refresh tokens expire if unused for 6 months
- The code automatically refreshes expired access tokens using the refresh token
- For truly non-expiring access, consider using Service Accounts (server-to-server only)
"""
import os
import sys
import json
from google_auth_oauthlib.flow import Flow, InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_PATH = 'client_secret.json'
TOKEN_PATH = 'token.json'


def main():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"Error: {CREDENTIALS_PATH} not found!")
        sys.exit(1)
    
    with open(CREDENTIALS_PATH, 'r') as f:
        creds_data = json.load(f)
    
    is_web_app = 'web' in creds_data
    is_installed_app = 'installed' in creds_data
    
    if not (is_web_app or is_installed_app):
        print("Error: Unknown OAuth client type. Expected 'web' or 'installed'.")
        sys.exit(1)
    
    # Setup flow
    redirect_uri = None
    if is_installed_app:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    else:
        redirect_uri = 'http://localhost:8080/'
        print(f"Using redirect URI: {redirect_uri}")
        print("Make sure this URI is added in Google Cloud Console.")
        input("Press Enter to continue...")
        flow = Flow.from_client_config(creds_data, SCOPES, redirect_uri=redirect_uri)
    
    # Authenticate
    try:
        if is_installed_app:
            creds = flow.run_local_server(port=0, open_browser=True)
        else:
            port = 8080
            creds = flow.run_local_server(port=port, open_browser=True)
    except Exception:
        # Manual flow for Docker/headless environments
        print("\nManual OAuth flow:")
        if is_web_app and redirect_uri:
            flow.redirect_uri = redirect_uri
        else:
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        
        auth_url, _ = flow.authorization_url(prompt='consent')
        print(f"\n1. Open this URL: {auth_url}")
        print("2. Authorize and copy the authorization code")
        
        code = input("\nEnter authorization code: ").strip()
        if not code:
            print("Error: Authorization code required!")
            sys.exit(1)
        
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    # Save token
    with open(TOKEN_PATH, 'w') as token:
        token.write(creds.to_json())
    
    print(f"\n✓ Token saved to {TOKEN_PATH}")


if __name__ == '__main__':
    main()

