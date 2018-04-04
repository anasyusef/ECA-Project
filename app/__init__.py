from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'auth.login'
mail = Mail(app)

from app.api import bp as api_bp
from app.auth import bp as auth_bp
from app.eca import bp as eca_bp

app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(eca_bp)


from app import routes, models
