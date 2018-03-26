import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY', 'AADNkSkgPHIrv0aZt3bsUtm6kPkxybIA0NDY0JsA0nT0FEfYmxuscCEkRK7J7pNV')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:12345678@localhost/ECAPROJECT'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
    MAIL_USE_TLS = bool(os.environ.get('MAIL_USE_TLS', 1))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'samenza2807@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['samenza2807@gmail.com']
