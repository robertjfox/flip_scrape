import smtplib
from email.message import EmailMessage


def send_email(email_config, subject: str, body: str):
    if not email_config.host or not email_config.sender or not email_config.recipient:
        return {"status": "skipped", "reason": "email config missing"}

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = email_config.sender
    msg["To"] = email_config.recipient
    msg.set_content(body)

    with smtplib.SMTP(email_config.host, email_config.port) as server:
        server.starttls()
        if email_config.user:
            server.login(email_config.user, email_config.password)
        server.send_message(msg)

    return {"status": "sent"}
