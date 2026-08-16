import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Dict
from config import SENDER_EMAIL, GMAIL_APP_PASSWORD

def send_outreach_email(
    recipient_email: str,
    subject: str,
    body_text: str,
    sender_email: str = "",
    app_password: str = ""
) -> Dict[str, any]:
    """
    Sends a cold outreach email via Gmail SMTP using SSL (port 465).
    """
    sender = sender_email or os.environ.get("SENDER_EMAIL", SENDER_EMAIL)
    pwd = app_password or os.environ.get("GMAIL_APP_PASSWORD", GMAIL_APP_PASSWORD)
    
    # Strip spaces from 16-character Gmail app password if present
    if pwd:
        pwd = pwd.replace(" ", "").strip()
        
    if not sender or not pwd:
        return {
            "success": False,
            "error": "Gmail SMTP credentials not configured. Please set your Gmail App Password in Email Setup."
        }
        
    if not recipient_email or "@" not in recipient_email:
        return {
            "success": False,
            "error": f"Invalid recipient email address: {recipient_email}"
        }
        
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr(("Talha Yousaf | E-Commerce Specialist", sender))
        msg["To"] = recipient_email.strip()
        msg["Subject"] = subject.strip()
        
        # Attach plain text
        msg.attach(MIMEText(body_text.strip(), "plain", "utf-8"))
        
        # Send via SSL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=12) as server:
            server.login(sender, pwd)
            server.sendmail(sender, recipient_email.strip(), msg.as_string())
            
        return {
            "success": True,
            "message": f"Email successfully delivered to {recipient_email}"
        }
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "error": "Gmail Authentication Failed: Please check your Gmail App Password (requires 2-Step Verification + App Password)."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send email: {str(e)}"
        }
