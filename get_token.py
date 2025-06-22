import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Only read/send emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    # Load your downloaded credentials.json
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    creds = flow.run_local_server(port=0)

    # Output refresh token and other details
    print("✅ REFRESH TOKEN GENERATED:")
    print(f"Refresh Token: {creds.refresh_token}")
    print(f"Client ID: {creds.client_id}")
    print(f"Client Secret: {creds.client_secret}")

    # Optional: Save token to token.json
    with open('token.json', 'w') as token_file:
        token_file.write(creds.to_json())

if __name__ == '__main__':
    main()