import json

from flask import request, abort
from flask_login import current_user, login_required

from app.api import bp
from app.decorators import check_user_confirmed
from app.models import Eca, User, Registration, Attendance


@bp.route('/view_attendance_detail/<eca_name>/<int:user_id>')
@login_required
@check_user_confirmed
def view_attendance_detail_api(eca_name, user_id):
    if current_user.role.name.lower() == 'student':
        if current_user.id != user_id:  # Checks that the student is only allowed to check his attendance
            abort(403)
    eca = Eca.query.filter_by(name=eca_name).first()
    user = User.query.filter_by(id=user_id).first()
    if current_user.role.name.lower() == 'teacher':  # This condition ensures that only teachers can look at students
        # joined into their ECA, other teachers cannot.
        if eca.user != current_user:
            abort(403)
    if eca_name.lower() == 'overall':
        registration_user = Registration.query.filter_by(user=user, in_waiting_list=False).first()
        user_attendance_true = len(Attendance.query.filter_by(registration=registration_user, attended=True).all())
        user_attendance_false = len(Attendance.query.filter_by(registration=registration_user, attended=False).all())
        user_attendance_total = len(Attendance.query.filter_by(registration=registration_user).all())
    else:
        if eca is not None:
            registration_user = Registration.query.filter_by(user=user, eca=eca, in_waiting_list=False).first()
            user_attendance_true = len(Attendance.query.filter_by(registration=registration_user, attended=True).all())
            user_attendance_false = len(Attendance.query.filter_by(registration=registration_user, attended=False).all())
            user_attendance_total = len(Attendance.query.filter_by(registration=registration_user).all())
        else:
            abort(404)

    return json.dumps({'attendance_true': user_attendance_true, 'attendance_false': user_attendance_false,
                       'attendance_total': user_attendance_total,
                       'percentage_attendance_true':
                           (user_attendance_true/(user_attendance_total if user_attendance_total != 0 else 1)) * 100,
                       'percentage_attendance_false':
                           (user_attendance_false/(user_attendance_total if user_attendance_total != 0 else 1)) * 100})


@bp.route('/eca_info')
@login_required
@check_user_confirmed
def eca_info():  # Following procedure's purpose is to deliver information to the front-end to work with AJAX
    eca = Eca.query.filter_by(name=request.args.get('eca')).first()
    # ECA is requested from the parameter sent in the URL
    # Parameters are got with request.args.get()
    if eca is not None:
        start_time = str(eca.datetime.start_time)
        end_time = str(eca.datetime.end_time)
        day = eca.datetime.day
        organiser = '{} {}'.format(eca.user.first_name, eca.user.last_name)
        location = eca.location
        max_people = eca.max_people
        max_waiting_list = eca.max_waiting_list
        brief_description = eca.brief_description
        essentials = eca.essentials
        email_address = eca.user.email
        students_enrolled = len(Registration.query.filter_by(eca=eca, in_waiting_list=False).all())
        students_in_waiting_list = len(Registration.query.filter_by(eca=eca, in_waiting_list=True).all())
        status = eca.is_active
        return json.dumps({'start_time': start_time, 'end_time': end_time,
                           'day': day.title(), 'organiser': organiser, 'location': location,
                           'students_enrolled': students_enrolled,
                           'max_people': max_people, 'students_in_waiting_list': students_in_waiting_list,
                           'max_waiting_list': max_waiting_list,
                           'brief_description': brief_description, 'essentials': essentials,
                           'email_address': email_address, 'status': status})
    abort(404)
