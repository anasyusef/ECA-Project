from flask_mail import Message
from app import mail, app
from flask import render_template, request
from threading import Thread


def send_async_email(arg_app, message):
    with arg_app.app_context():
        mail.send(message)


def send_email(subject, recipients, html_body, sender=app.config['ADMINS'][0], users=None, **kwargs):

    message = Message(subject=subject, recipients=recipients,
                      sender=sender)
    if request.path.startswith('/eca/delete'):  # This is to make sure that the following code is triggered when an eca
        # is going to be removed
        with mail.connect() as conn:
            for i in range(len(users)):
                message = Message(subject=subject, recipients=[recipients[i]],
                                  sender=sender)
                message.html = render_template(html_body + '.html', user=users[i], **kwargs)
                conn.send(message)
    elif request.path.startswith('/notification_eca'): # This is to make sure that the following code is triggered when
        #  a notification of eca is sent

        with mail.connect() as conn:
            for i in range(len(users)):
                message = Message(subject=subject, recipients=[recipients[i]],
                                  sender=sender)
                message.html = render_template(html_body + '.html', user=users[i], **kwargs)
                conn.send(message)

    else:
        message.html = render_template(html_body + '.html', **kwargs)
        mail.send(message)

    Thread(target=send_async_email, args=(app, message)).start()
