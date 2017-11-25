import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(subject, content, receivers):
    my_account = {yourEmail}
    my_password = {yourPassword}

    COMMA_SEPORATOR = ', '
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = my_account
    msg['To'] = COMMA_SEPORATOR.join(receivers)
    part1 = MIMEText(content, 'plain')
    msg.attach(part1)

    s = smtplib.SMTP('{yourMailServer}')
    s.login(my_account, my_password)
    s.sendmail(my_account, receivers, msg.as_string())
    s.quit()
