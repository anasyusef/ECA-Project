from app.models import *

@app.shell_context_processor
def make_shell_context():
    """
    The keys on the dictionary can be used on the shell within the app context.
    :return:
    """
    return {'db': db, 'User': User, 'Role': Role, 'Eca': Eca, 'Datetime': Datetime, 'Registration': Registration,
            'WaitingList': WaitingList, 'Attendance': Attendance, 'setup_db': setup_db}
