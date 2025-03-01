import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailService:
    def __init__(self):
        try:
            self.session = smtplib.SMTP('smtp.gmail.com', 587)
            self.session.starttls()
            self.sender = "eMonitoringAI@gmail.com"
            self.sender_password = "pqjuschmtiuxxaec"
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