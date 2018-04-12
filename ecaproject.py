from app.models import *

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Role': Role, 'Eca': Eca, 'Datetime': Datetime, 'Registration': Registration,
            'WaitingList': WaitingList, 'Attendance': Attendance}