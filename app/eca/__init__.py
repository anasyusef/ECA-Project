from flask import Blueprint

bp = Blueprint('eca', __name__, url_prefix='/eca')

from app.eca import eca

