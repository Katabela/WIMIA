import os
import base64
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader

# Load .env values
load_dotenv()

# Gmail OAuth credentials
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN")

# Updated path to match your new project
env = Environment(loader=FileSystemLoader("app/email_templates"))


def render_email_template(template_name, **kwargs):
    """Render a Jinja2 email template."""
    template = env.get_template(template_name)
    return template.render(**kwargs)


def send_email(to_email, subject, template_name, **kwargs):
    """Send an email via the Gmail API with a rendered HTML template."""
    creds = Credentials.from_authorized_user_info(
        {
            "client_id": GMAIL_CLIENT_ID,
            "client_secret": GMAIL_CLIENT_SECRET,
            "refresh_token": GMAIL_REFRESH_TOKEN,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )

    # Build the Gmail API service
    service = build("gmail", "v1", credentials=creds)

    # Render template
    email_body = render_email_template(template_name, **kwargs)

    # Build MIME message
    message = MIMEText(email_body, "html")
    message["to"] = to_email
    message["subject"] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    try:
        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
