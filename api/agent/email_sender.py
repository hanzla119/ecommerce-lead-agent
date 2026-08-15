import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from config import SENDER_EMAIL, GMAIL_APP_PASSWORD

def send_outreach_email(
    to_email: str,
    subject: str,
    body_text: str,
    sender_email: str = "",
    app_password: str = ""
) -> Dict[str, any]:
    """
    Sends a direct cold outreach email using Gmail SMTP (smtp.gmail.com:587).
    Requires a Google App Password (16 characters from Google Account -> Security -> App Passwords).
    """
    from_addr = sender_email.strip() if sender_email else SENDER_EMAIL
    pwd = app_password.strip().replace(" ", "") if app_password else GMAIL_APP_PASSWORD.replace(" ", "")
    
    if not to_email or "@" not in to_email:
        return {"success": False, "error": "Invalid recipient email address"}
        
    if not from_addr or "@" not in from_addr:
        return {"success": False, "error": "Sender email not configured"}
        
    if not pwd:
        return {
            "success": False, 
            "error": "Google App Password missing. Please enter your 16-character Google App Password in Settings."
        }
        
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"Talha Yousaf <{from_addr}>"
        msg["To"] = to_email.strip()
        msg["Subject"] = subject.strip()
        
        # Attach plain text
        part = MIMEText(body_text.strip(), "plain", "utf-8")
        msg.attach(part)
        
        # Connect to Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        server.ehlo()
        server.starttls()
        server.login(from_addr, pwd)
        server.sendmail(from_addr, [to_email.strip()], msg.as_string())
        server.quit()
        
        return {
            "success": True, 
            "message": f"Email successfully delivered to {to_email} from {from_addr}"
        }
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False, 
            "error": "Gmail Authentication Failed: Invalid App Password. Generate a 16-char App Password at myaccount.google.com/apppasswords"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to send email: {str(e)}"}

if __name__ == "__main__":
    print("Testing email sender module configuration...")
