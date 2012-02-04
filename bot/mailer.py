#coding=utf-8

import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

class Mailer:
    def send(self, mfrom_name, mfrom_address, mtos, subject, text, html):
        if not len(mtos):
            return
        msg = MIMEMultipart('alternative')

        msg['Subject'] = Header(subject, 'utf-8').encode()
        msg['From'] = Header(mfrom_name, 'utf-8').encode() + " " + mfrom_address
        msg['To'] = ",".join(mtos)

        part1 = MIMEText(text, 'plain', 'utf-8')
        #part2 = MIMEText(html, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part1)
        s = smtplib.SMTP('localhost')
        s.sendmail(mfrom_address, mtos, msg.as_string())
        s.quit()
