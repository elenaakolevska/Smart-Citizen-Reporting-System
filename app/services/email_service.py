import smtplib
from email.mime.text import MIMEText
from app.models.email_log import EmailLog
from app.db.session import SessionLocal
import os
from app.models.email_log import EmailLog
from app.db.session import SessionLocal


def send_email(to_email: str, subject: str, content: str):
    if "@" not in to_email:
        print("Invalid email")
        return

    msg = MIMEText(content, "html")
    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = to_email

    db = SessionLocal()

    status = "sent"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(
                os.getenv("EMAIL_USER"),
                os.getenv("EMAIL_PASS")
            )
            server.sendmail(
                os.getenv("EMAIL_USER"),
                to_email,
                msg.as_string()
            )

        print("Email sent successfully")

    except Exception as e:
        print("Email error:", e)
        status = "failed"

    # 👉 SAVE LOG
    log = EmailLog(
        to_email=to_email,
        subject=subject,
        status=status
    )

    db.add(log)
    db.commit()
    db.close()


def build_report_email(description: str):
    return f"""
    <div style="background-color:#f4f6f8; padding:20px; font-family:Arial, sans-serif;">

        <div style="max-width:600px; margin:auto; background:white; border-radius:10px; padding:20px;">

            <!-- LOGO -->
            <div style="text-align:center; margin-bottom:20px;">
                <img src="https://cdn-icons-png.flaticon.com/512/1828/1828640.png" 
                     alt="Logo" width="60" />
            </div>

            <!-- TITLE -->
            <h2 style="color:#2c3e50; text-align:center;">
                🚨 New Report Created
            </h2>

            <!-- CONTENT -->
            <p style="font-size:16px; color:#333;">
                <b>Description:</b> {description}
            </p>

            <hr style="margin:20px 0;">

            <!-- BUTTON -->
            <div style="text-align:center; margin:20px 0;">
                <a href="http://localhost:8000/docs"
                   style="background:#3498db; color:white; padding:12px 20px; text-decoration:none; border-radius:5px;">
                   View Report
                </a>
            </div>

            <!-- FOOTER -->
            <p style="font-size:12px; color:gray; text-align:center;">
                Smart Citizen Reporting System
            </p>

            <!-- UNSUBSCRIBE -->
            <p style="font-size:12px; text-align:center;">
                <a href="http://localhost:8000/unsubscribe">
                    Unsubscribe
                </a>
            </p>

        </div>
    </div>
    """