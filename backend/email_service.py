import os
import smtplib
from email.message import EmailMessage

def send_email(to, subject, body):
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    # No email settings yet: print the email in the terminal instead
    if not user or not password:
        print("\n===== EMAIL (console mode) =====")
        print(f"To: {to}\nSubject: {subject}\n\n{body}")
        print("================================\n")
        return

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, password)
        server.send_message(msg)