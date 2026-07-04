import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

SMTP_HOST = os.environ.get("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 1025))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
EMAILS_FROM = os.environ.get("EMAILS_FROM", "noreply@posh-platform.com")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:80")


def get_smtp_security_options() -> dict:
    """
    MailHog:
        SMTP_HOST=mailhog
        SMTP_PORT=1025
        use_tls=False
        start_tls=False

    Gmail STARTTLS:
        SMTP_HOST=smtp.gmail.com
        SMTP_PORT=587
        use_tls=False
        start_tls=True

    Gmail SSL:
        SMTP_HOST=smtp.gmail.com
        SMTP_PORT=465
        use_tls=True
        start_tls=False
    """
    if SMTP_HOST == "mailhog":
        return {
            "use_tls": False,
            "start_tls": False,
        }

    if SMTP_PORT == 465:
        return {
            "use_tls": True,
            "start_tls": False,
        }

    return {
        "use_tls": False,
        "start_tls": True,
    }


async def send_email(
    to: str,
    subject: str,
    html_body: str,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> None:
    """
    attachments format:
    [
        ("certificate_123.pdf", pdf_bytes, "pdf")
    ]
    """
    message_type = "mixed" if attachments else "alternative"
    message = MIMEMultipart(message_type)

    message["From"] = EMAILS_FROM
    message["To"] = to
    message["Subject"] = subject

    message.attach(MIMEText(html_body, "html"))

    if attachments:
        for filename, file_bytes, subtype in attachments:
            attachment = MIMEApplication(file_bytes, _subtype=subtype)
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=filename,
            )
            message.attach(attachment)

    smtp_options = get_smtp_security_options()

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER if SMTP_USER else None,
        password=SMTP_PASSWORD if SMTP_PASSWORD else None,
        use_tls=smtp_options["use_tls"],
        start_tls=smtp_options["start_tls"],
    )


async def send_otp_email(to: str, first_name: str, otp: str) -> None:
    subject = "Your POSH Platform Verification Code"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1a3c5e;">POSH Training Platform</h2>
        <p>Dear {first_name},</p>
        <p>Your verification code is:</p>
        <div style="background: #f5f5f5; padding: 20px; text-align: center;
                    font-size: 36px; font-weight: bold; letter-spacing: 10px;
                    color: #1a3c5e; border-radius: 8px; margin: 20px 0;">
            {otp}
        </div>
        <p>This code expires in <strong>10 minutes</strong>.</p>
        <p>If you did not request this, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">POSH Training Platform</p>
    </div>
    """

    await send_email(to, subject, html)


async def send_password_reset_email(to: str, first_name: str, reset_token: str) -> None:
    reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    subject = "Reset Your POSH Platform Password"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1a3c5e;">Password Reset Request</h2>
        <p>Dear {first_name},</p>
        <p>
            Click the button below to reset your password.
            This link expires in <strong>1 hour</strong>.
        </p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}"
               style="background: #1a3c5e; color: white; padding: 14px 28px;
                      text-decoration: none; border-radius: 6px; font-size: 16px;">
                Reset Password
            </a>
        </div>

        <p>Or copy this link: <a href="{reset_url}">{reset_url}</a></p>
        <p>If you did not request a password reset, please ignore this email.</p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">POSH Training Platform</p>
    </div>
    """

    await send_email(to, subject, html)


async def send_welcome_email(to: str, first_name: str, temp_password: str) -> None:
    login_url = f"{FRONTEND_URL}/login"
    subject = "Welcome to POSH Training Platform"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1a3c5e;">Welcome to POSH Training Platform</h2>
        <p>Dear {first_name},</p>
        <p>
            Your account has been created. Please log in using the details below
            and change your password immediately.
        </p>

        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px;
                    margin: 20px 0;">
            <p>
                <strong>Login URL:</strong>
                <a href="{login_url}">{login_url}</a>
            </p>
            <p><strong>Email:</strong> {to}</p>
            <p>
                <strong>Temporary Password:</strong>
                <code style="background: #e8e8e8; padding: 4px 8px;
                             border-radius: 4px;">
                    {temp_password}
                </code>
            </p>
        </div>

        <p style="color: #e74c3c;">
            Please change your password after first login.
        </p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">POSH Training Platform</p>
    </div>
    """

    await send_email(to, subject, html)


async def send_certificate_email(
    to: str,
    first_name: str,
    course_name: str,
    cert_number: str,
    pdf_bytes: bytes,
) -> None:
    subject = f"Your POSH Training Certificate - {course_name}"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1a3c5e;">Congratulations!</h2>
        <p>Dear {first_name},</p>
        <p>
            You have successfully completed the POSH training course
            <strong>{course_name}</strong>.
        </p>
        <p>Your certificate is attached to this email.</p>

        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px;
                    margin: 20px 0;">
            <p><strong>Certificate Number:</strong> {cert_number}</p>
        </div>

        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">POSH Training Platform</p>
    </div>
    """

    await send_email(
        to=to,
        subject=subject,
        html_body=html,
        attachments=[
            (
                f"certificate_{cert_number}.pdf",
                pdf_bytes,
                "pdf",
            )
        ],
    )