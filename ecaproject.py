from app import app, db
from app.models import User, Role, Eca, Datetime, Registration


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Role': Role, 'Eca': Eca, 'Datetime': Datetime, 'Registration':Registration}