import aiosmtplib
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM     = os.getenv("SMTP_FROM", "")

MAX_RETRIES   = 2
RETRY_DELAY   = 10  # seconds between retries


async def send_email(to: str, subject: str, body_html: str) -> bool:
    """Send an email. Returns True if successful, False if all retries fail."""
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"]    = f"IGP Office EVSU <{SMTP_FROM}>"
    message["To"]      = to
    message.attach(MIMEText(body_html, "html"))

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await aiosmtplib.send(
                message,
                hostname=SMTP_HOST,
                port=SMTP_PORT,
                username=SMTP_USER,
                password=SMTP_PASSWORD,
                start_tls=True,
            )
            return True
        except Exception as e:
            print(f"[EMAIL] Attempt {attempt} failed for {to}: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)

    return False


def build_inquiry_response_email(
    student_name:     str,
    product_name:     str,
    response_message: str,
    responded_at:     str,
    inquiry_message:  str,
) -> str:
    """Build the HTML email body for inquiry responses."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">
        <div style="background:#8B1A1A; padding: 20px; text-align:center;">
            <h2 style="color:#E8C96A; margin:0;">EVSU IGP Office</h2>
            <p style="color:#fff; margin:4px 0 0;">Product Inquiry Response</p>
        </div>
        <div style="padding: 24px;">
            <p>Dear <strong>{student_name}</strong>,</p>
            <p>We have received your inquiry regarding <strong>{product_name}</strong>
            and would like to provide you with the following response:</p>

            <div style="background:#F5EDD0; border-left: 4px solid #C9A84C;
                        padding: 14px 18px; border-radius: 4px; margin: 16px 0;">
                <p style="margin:0;">{response_message}</p>
            </div>

            <hr style="border:none; border-top:1px solid #eee; margin: 20px 0;">

            <p style="font-size:12px; color:#888;">
                <strong>Your original inquiry:</strong><br>
                {inquiry_message}
            </p>
            <p style="font-size:12px; color:#888;">
                <strong>Response sent:</strong> {responded_at}
            </p>
        </div>
        <div style="background:#f5f5f5; padding:14px; text-align:center;
                    font-size:11px; color:#aaa;">
            This is an automated message from the EVSU IGP Product Inquiry System.
            Please do not reply to this email.
        </div>
    </body>
    </html>
    """
