import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

class EmailService:
    def __init__(self):
        try:
            self.session = smtplib.SMTP('smtp.gmail.com', 587)
            self.session.starttls()
            self.sender = os.getenv("SENDER_EMAIL")
            self.sender_password = os.getenv("SENDER_PASSWORD")
            self.session.login(self.sender, self.sender_password)
            print("Login sucessfuly into server mail.")
        except Exception as e:
            print(e)

    def send_code_verification(self, to, code):
        message = MIMEMultipart()
        message['From'] = self.sender
        message['To'] = to
        message['Subject'] = 'Verification code - eMonitoringAI'
        message.attach(MIMEText(f'Your verification code is: {code}', 'plain'))
        try:
            self.session.sendmail(self.sender, to, message.as_string())
            print("Email sent sucessfuly")
        except Exception as e:
            print("Error after sending:", e)

emailService = None
def get_email_service():
    global emailService
    if emailService == None:
        emailService = EmailService()
    return emailService