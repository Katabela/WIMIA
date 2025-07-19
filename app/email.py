import os
import base64
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from jinja2 import Environment, FileSystemLoader

# Load .env values
load_dotenv()

GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN")
EMAIL_SENDER = os.getenv("EMAIL_SENDER") or "no-reply@WIMIA.com"
EMAIL_SENDER_NAME = "WIMIA Team"  # or os.getenv("EMAIL_SENDER_NAME")

env = Environment(loader=FileSystemLoader("app/email_templates"))

def render_email_template(template_name, **kwargs):
    try:
        template = env.get_template(template_name)
        return template.render(**kwargs)
    except Exception as e:
        print(f"Template rendering error: {e}")
        return "<p>Error loading template</p>"

def send_email(to_email, subject, template_name, **kwargs):
    creds = Credentials.from_authorized_user_info({
        "client_id": GMAIL_CLIENT_ID,
        "client_secret": GMAIL_CLIENT_SECRET,
        "refresh_token": GMAIL_REFRESH_TOKEN,
        "token_uri": "https://oauth2.googleapis.com/token",
    })

    try:
        service = build("gmail", "v1", credentials=creds)

        html_body = render_email_template(template_name, **kwargs)
        subject = subject.replace("\n", "").replace("\r", "")

        raw_message = base64.urlsafe_b64encode(
            f"From: {EMAIL_SENDER_NAME} <{EMAIL_SENDER}>\r\n"
            f"To: {to_email}\r\n"
            f"Subject: {subject}\r\n"
            f"Content-Type: text/html; charset=UTF-8\r\n\r\n"
            f"{html_body}".encode("utf-8")
        ).decode("utf-8")

        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        print(f"✅ Email sent to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
