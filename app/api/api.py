from app.api import bp
from flask_login import current_user, login_required
from flask import request
from app.models import Eca, User, Registration, Attendance
import json


@bp.route('/view_attendance_detail/<eca_name>/<int:user_id>')
@login_required
def view_attendance_detail_api(eca_name, user_id):
    # TODO allow access to teachers that have the student registered to their ECA. However, do not allow other teachers
    if current_user.role.name.lower() == 'student':
        if current_user.id != user_id:
            return "You are not allowed to see this page", 403
    eca = Eca.query.filter_by(name=eca_name).first()
    user = User.query.filter_by(id=user_id).first()
    if eca_name.lower() == 'overall':
        registration_user = Registration.query.filter_by(user=user).first()
        user_attendance_true = len(Attendance.query.filter_by(registration=registration_user, attended=True).all())
        user_attendance_false = len(Attendance.query.filter_by(registration=registration_user, attended=False).all())
        user_attendance_total = len(Attendance.query.filter_by(registration=registration_user).all())
    else:
        if eca is not None:
            registration_user = Registration.query.filter_by(user=user, eca=eca).first()
            user_attendance_true = len(Attendance.query.filter_by(registration=registration_user, attended=True).all())
            user_attendance_false = len(Attendance.query.filter_by(registration=registration_user, attended=False).all())
            user_attendance_total = len(Attendance.query.filter_by(registration=registration_user).all())
        else:
            return "ECA Not Found"

    return json.dumps({'attendance_true': user_attendance_true, 'attendance_false': user_attendance_false,
                       'attendance_total': user_attendance_total,
                       'percentage_attendance_true':
                           (user_attendance_true/(user_attendance_total if user_attendance_total != 0 else 1)) * 100,
                       'percentage_attendance_false':
                           (user_attendance_false/(user_attendance_total if user_attendance_total != 0 else 1)) * 100})


@bp.route('/eca_info')
@login_required
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
        students_enrolled = len(eca.registration)
        students_in_waiting_list = len(eca.waiting_list)
        return json.dumps({'start_time': start_time, 'end_time': end_time,
                           'day': day.title(), 'organiser': organiser, 'location': location,
                           'students_enrolled': students_enrolled,
                           'max_people': max_people, 'students_in_waiting_list': students_in_waiting_list,
                           'max_waiting_list': max_waiting_list,
                           'brief_description': brief_description, 'essentials': essentials,
                           'email_address': email_address})
    return 'ECA not found', 404
