import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import secrets
import os


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


        image_path = os.path.join("static", "media", "reset password.png")
        image_url = "/static/media/reset%20password.png"

        msg = MIMEMultipart()
        msg['From'] = "noreply@geometricakinator.com"
        msg['To'] = email
        msg['Subject'] = "איפוס סיסמה - Geometric Akinator"

        reset_link = f"http://127.0.0.1:10000/login/reset-password/{reset_token}"

        body = f"""
            <html>
                <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: Arial, sans-serif;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <tr>
                            <td style="padding: 40px 30px;" dir="rtl">
                                <!-- Logo or Header Image could go here -->
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td style="text-align: center; padding-bottom: 30px;">
                                            <h1 style="color: #3F4D57; margin: 0; font-size: 24px;">איפוס סיסמה</h1>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Email Content -->
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td style="padding: 20px 0 5px 0; text-align: right;">  <!-- Reduced bottom padding to 5px -->
                                            <p style="color: #666666; font-size: 16px; line-height: 1.5; margin: 0 0 20px;">שלום,</p>
                                            <p style="color: #666666; font-size: 16px; line-height: 1.5; margin: 0;">קיבלנו בקשה לאיפוס הסיסמה שלך בGeometric Akinator.</p>  <!-- Removed bottom margin -->
                                        </td>
                                    </tr>
                                    <!-- Reset Password Image Link -->
                                    <tr>
                                        <td style="padding: 5px 0 20px 0; text-align: center;">  <!-- Reduced top padding to 5px -->
                                            <a href="{reset_link}">
                                                <img src="http://127.0.0.1:10000/static/media/reset password.png" 
                                                     alt="איפוס סיסמה" 
                                                     style="max-width: 200px; height: auto; cursor: pointer;">
                                            </a>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 20px 0; text-align: right;">
                                            <p style="color: #666666; font-size: 14px; line-height: 1.5; margin: 0 0 10px;">הקישור תקף למשך שעה אחת.</p>
                                            <p style="color: #666666; font-size: 14px; line-height: 1.5; margin: 0;">אם לא ביקשת לאפס את הסיסמה, אנא התעלם מהודעה זו.</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
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