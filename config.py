import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY', 'SOMETHING-VERY-DIFFICULT')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:12345678@127.0.0.1/ecaproject2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_HOST', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = bool(os.environ.get('MAIL_USE_TLS', 1))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'anas.y0807@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'sliford123')
    ADMINS = ['ecap@gmail.com']
