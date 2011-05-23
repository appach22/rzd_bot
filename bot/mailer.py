#coding=utf-8

import smtplib

from email.mime.text import MIMEText
from email.header import Header

class Mailer:
    def send(self, mfrom_name, mfrom_address, mtos, subject, type, text):
        if not len(mtos):
            return
        msg = MIMEText(text, type, 'utf-8')

        msg['Subject'] = Header(subject, 'utf-8').encode()
        msg['From'] = Header(mfrom_name, 'utf-8').encode() + " " + mfrom_address
        msg['To'] = ",".join(mtos)

        s = smtplib.SMTP('localhost')
        s.sendmail(mfrom_address, mtos, msg.as_string())
        s.quit()
