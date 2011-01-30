
import smtplib

from email.mime.text import MIMEText
from email.header import Header

class Mailer:
    def send(self, mfrom, mto, subject, type, text):
        msg = MIMEText(text, type, 'utf-8')

        msg['Subject'] = Header(subject, 'utf-8').encode()
        msg['From'] = mfrom
        msg['To'] = mto

        s = smtplib.SMTP('localhost')
        s.sendmail(mfrom, mto, msg.as_string())
        s.quit()
