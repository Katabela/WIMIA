import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES
    )

    # This starts a local server on port 8080 and catches the redirect
    creds = flow.run_local_server(port=8080)

    print("\n✅ REFRESH TOKEN GENERATED:")
    print("Refresh Token:", creds.refresh_token)
    print("Access Token:", creds.token)
    print("Client ID:", creds.client_id)
    print("Client Secret:", creds.client_secret)

    # Save token to token.json (optional)
    with open("token.json", "w") as token_file:
        token_file.write(creds.to_json())

if __name__ == "__main__":
    main()
