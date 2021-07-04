import smtplib

gmail_user = 'fyellin@gmail.com'
gmail_password = '..............'

def send_mail(email_to_list, subject, body):
    email_text = f"""\
From: {gmail_user}
To: {", ".join(email_to_list)}
Subject: {subject}

{body}
"""
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(email_to_list, email_text)
        server.close()
        return True
    except:
        return False


def run():
  mail = 'abcdefghijklmnopqrstuvwxyz\n' *  100
  send_mail(["fy@fyellin.com", "shamfy@gmail.com"], "This is a test", mail)

if __name__ == '__main__':
  run()
