import smtplib
from email.mime.text import MIMEText

def send_mail(customer, dealer, rating, comments):
    port = 2525
    smtp_server = 'smtp.mailtrap.io'
    login = 'd4c1b0892d1932'
    password = '7e9533640f797d'
    message = "<h3> New Feedback Submission </h3><ul><li>Dealer: {}</li> <li>Rating: {}</li> <li>Comments: {}</li></ul>".format(dealer, rating, comments)

    sender_email = "nottootechy@mail.com"
    receiver_email = "myklenovica@gmail.com"
    msg = MIMEText(message, 'html')
    msg['Subject'] = 'Lexus Feedback'
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Send email1
    with smtplib.SMTP(smtp_server, port) as server:
        server.login(login, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
