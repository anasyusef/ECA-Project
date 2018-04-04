import datetime
from app import app, emails
from app.models import User, Eca, Registration, Attendance, WaitingList
from flask import render_template, redirect, url_for, flash, request
from app.forms import JoinEca, NotificationEca
from flask_login import current_user, login_required
from app import db
from app.decorators import permission_required, check_user_confirmed
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError


@app.route('/')
@check_user_confirmed
def index():
    if current_user.is_authenticated:
        if current_user.role.name.lower() == 'teacher':
            ecas_by_user = Eca.query.filter_by(user=current_user).all()
            return render_template('teacher_dashboard.html', title="Teacher's Dashboard",
                                   num_ecas_by_user=len(ecas_by_user),
                                   ecas_by_user=ecas_by_user, day_name_today=datetime.datetime.now().strftime('%A'),
                                   today_eca=Eca.query.filter_by(user=current_user).all())
        elif current_user.role.name.lower() == 'student':
            registrations_by_user = Registration.query.filter_by(user=current_user).all()
            waiting_lists_by_user = WaitingList.query.filter_by(user=current_user).all()
            return render_template('student_dashboard.html',
                                   title="Student's Dashboard", registrations_by_user=registrations_by_user,
                                   current_user=current_user, waiting_lists_by_user=waiting_lists_by_user)

    return redirect(url_for('auth.login'))


@app.route('/eca/take_attendance/<eca_name>')
@login_required
@permission_required('Teacher')
def take_attendance(eca_name):
    eca = Eca.query.filter_by(name=eca_name).first()

    if eca is None:
        return "ECA Not Found", 404

    if eca.user != current_user:
        flash("You are not allowed to take attendance on this ECA", 'danger')
        return redirect(url_for('eca.manage_ecas'))

    if eca.datetime.day != datetime.date.today().strftime('%A').lower():
        flash('You cannot take attendance since the ECA is not taking place today', 'danger')
        return redirect(url_for('eca.manage_ecas'))
    return render_template('take_attendance.html', eca=eca, Attendance=Attendance, today=datetime.date.today())


@app.route('/record_attendance')
@login_required
def record_attendance():
    eca = Eca.query.filter_by(name=request.args.get('eca')).first()
    # ECA is requested from the parameter sent in the URL
    # Parameters are got with request.args.get()
    if eca is not None:
        user_choice = request.args.get('attended').split('-')  # First item is the id of the user, second item
        # is the choice, for example [3, 'no']
        user = User.query.filter_by(id=user_choice[0]).first()
        registration_user = Registration.query.filter_by(user=user, eca=eca).first()
        if Attendance.query.filter_by(registration=registration_user, date=datetime.date.today()).first() is None:
            #  This is to ensure that attendance entries are not duplicated
            attendance_record = Attendance()
            attendance_record.registration = registration_user
            attendance_record.attended = True if user_choice[1] == 'yes' else False
            attendance_record.date = datetime.date.today()
            db.session.add(attendance_record)
            db.session.commit()
        else:
            return "Already registered attendance"

    return "Attendance Registered"


@app.route('/eca/view_attendance/<eca_name>/', defaults={'user_id': None})
@app.route('/eca/view_attendance/<eca_name>/<int:user_id>')
@login_required
def view_attendance(eca_name, user_id):
    eca = Eca.query.filter_by(name=eca_name).first()
    if user_id is not None:  # Checks if parameters were passed to the URL
        user = User.query.filter_by(id=user_id).first()  # If parameters were passed then find the
        # value of the parameter and check if it is on the database,
        # it is assumed that the value is the id of the user
        if user is not None and user in [registration.user for registration in eca.registration]:  # Checks that the
            # user is found (not None) and if the user is registered
            # in the eca selected. 'user' will return None when
            # nothing is found
            registration_user = Registration.query.filter_by(user=user, eca=eca).first()
            if current_user.role.name.lower() == 'student':
                if user_id != current_user.id:
                    # If the user is a student, then he should only be able to see attendance on his ECAs, therefore
                    # if he changes the URL then an error or warning should be shown to the user indicating that he
                    # is not allowed to access to this page
                    # That is why we first check that the user is a student, then we check if the id of the student
                    # is not equal to the id on the parameter, if that is true the error below is shown
                    flash('You are not allowed to go to this page', 'danger')
                    return redirect(url_for('attendance_eca'))
            return render_template('view_attendance_detail.html',
                                   attendance_info=Attendance.query.filter_by(registration=registration_user)
                                   .order_by(desc(Attendance.date)), eca=eca, user=user)
        else:
            if current_user.role.name.lower() == 'teacher':  # This is done for security purposes, so that students
                # cannot see who is in an ECA and who is not
                flash('This user is not in this ECA' if current_user.role.name.lower() == 'teacher'
                      else 'You are not allowed to go to this page', 'danger')

            return redirect(url_for('attendance_eca'))
    if eca is None:
        return "ECA Not Found", 404

    if eca.user != current_user:
        flash("You are not allowed to view attendance on this ECA", 'danger')
        return redirect(url_for('attendance_eca'))

    return render_template('view_attendance.html', Attendance=Attendance, eca=eca)
