from flask_mail import Message
from app import mail, app
from flask import render_template, request
from threading import Thread
import time


def send_async_email(arg_app, message):
    with arg_app.app_context():
        mail.send(message)


def send_email(subject, recipients, html_body, sender=app.config['ADMINS'][0], users=None, **kwargs):

    message = Message(subject=subject, recipients=recipients,
                      sender=sender)
    if users is not None:
        for i in range(len(users)):
            message = Message(subject=subject, recipients=[recipients[i]],
                              sender=sender)
            message.html = render_template(html_body + '.html', user=users[i], **kwargs)
            Thread(target=send_async_email, args=(app, message)).start()
    else:
        message.html = render_template(html_body + '.html', **kwargs)
        Thread(target=send_async_email, args=(app, message)).start()
