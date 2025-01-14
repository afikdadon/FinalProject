import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import secrets


class EmailUtils:
    @staticmethod
    def generate_reset_token():
        """Generate a secure random token for password reset"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def get_token_expiry():
        """Get expiry time for reset token (1 hour from now)"""
        return datetime.now() + timedelta(hours=1)

    @staticmethod
    def send_reset_email(email, reset_token):
        """Send password reset email using Mailtrap"""
        # Mailtrap credentials
        SMTP_SERVER = "sandbox.smtp.mailtrap.io"
        SMTP_PORT = 2525
        SMTP_USERNAME = "a2769d763a80f3"
        SMTP_PASSWORD = "a79000ef963db9"

        msg = MIMEMultipart()
        msg['From'] = "noreply@geometricakinator.com"
        msg['To'] = email
        msg['Subject'] = "איפוס סיסמה - Geometric Akinator"

        reset_link = f"http://127.0.0.1:10000/login/reset-password/{reset_token}"

        body = f"""
        <html>
            <body dir="rtl" style="font-family: Arial, sans-serif;">
                <h2>בקשת איפוס סיסמה</h2>
                <p>קיבלנו בקשה לאיפוס הסיסמה שלך.</p>
                <p>לחץ על הקישור הבא כדי לאפס את הסיסמה:</p>
                <p><a href="{reset_link}">איפוס סיסמה</a></p>
                <p>הקישור תקף למשך שעה אחת.</p>
                <p>אם לא ביקשת לאפס את הסיסמה, אנא התעלם מהודעה זו.</p>
            </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html', 'utf-8'))

        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False