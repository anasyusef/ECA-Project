from flask import redirect, url_for, render_template
from flask_login import login_required
from sqlalchemy import desc, asc

from app.attendance import bp
from app.decorators import permission_required
from app.forms import *
from app.models import *


@bp.route('/take_attendance/<eca_name>')
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


@bp.route('/eca/view_attendance/<eca_name>/', defaults={'user_id': None}, methods=['GET', 'POST'])
@bp.route('/eca/view_attendance/<eca_name>/<int:user_id>')
@login_required
def view_attendance(eca_name, user_id):
    eca = Eca.query.filter_by(name=eca_name).first()
    form = SortBy()
    # By default the students are ordered by their first name
    ordered_registrations = Registration.query.filter_by(eca=eca).join(User).order_by(asc(User.first_name)).all()
    # If the user has decided to change the order, then the form.validate_on_submit() function will be triggered
    # depending on the choice of the user the students will be sorted accordingly

    if form.validate_on_submit():
        if form.sort_by.data.lower() == 'first_name':
            ordered_registrations = Registration.query.filter_by(eca=eca).join(User).\
                order_by(asc(User.first_name)).all()
        elif form.sort_by.data.lower() == 'last_name':
            ordered_registrations = Registration.query.filter_by(eca=eca).join(User). \
                order_by(asc(User.last_name)).all()
        elif form.sort_by.data.lower() == 'highest_attendance':
            ordered_registrations = Registration.query.filter_by(eca=eca).join(Attendance)\
                .order_by(desc(Attendance.attended))
        elif form.sort_by.data.lower() == 'lowest_attendance':
            ordered_registrations = Registration.query.filter_by(eca=eca).join(Attendance) \
                .order_by(asc(Attendance.attended))

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
                    return redirect(url_for('attendance.attendance_eca'))
            return render_template('view_attendance_detail.html',
                                   attendance_info=Attendance.query.filter_by(registration=registration_user)
                                   .order_by(desc(Attendance.date)),  ordered_registrations=ordered_registrations,
                                   user=user, eca=eca, form=form)
        else:
            if current_user.role.name.lower() == 'teacher':  # This is done for security purposes, so that students
                # cannot see who is in an ECA and who is not
                flash('This user is not in this ECA' if current_user.role.name.lower() == 'teacher'
                      else 'You are not allowed to go to this page', 'danger')

            return redirect(url_for('attendance.attendance_eca'))
    if eca is None:
        return "ECA Not Found", 404

    if eca.user != current_user:
        flash("You are not allowed to view attendance on this ECA", 'danger')
        return redirect(url_for('attendance.attendance_eca'))

    return render_template('view_attendance.html', Attendance=Attendance, Registration=Registration,
                           eca=eca, form=form, ordered_registrations=ordered_registrations)


@bp.route('/record_attendance/<eca_name>/<attended>/<int:user_id>')
@login_required
@permission_required('Teacher')
def record_attendance(eca_name, attended, user_id):
    eca = Eca.query.filter_by(name=eca_name).first()
    # ECA is requested from the parameter sent in the URL
    # Parameters are got with request.args.get()
    if eca.user != current_user:
        return "You are not allowed to do this action", 403

    if eca is not None:
        user = User.query.get(user_id)
        registration_user = Registration.query.filter_by(user=user, eca=eca).first()
        if Attendance.query.filter_by(registration=registration_user, date=datetime.date.today()).first() is None:
            #  This is to ensure that attendance entries are not duplicated
            attendance_record = Attendance()
            attendance_record.registration = registration_user
            attendance_record.attended = True if attended == 'yes' else False
            attendance_record.date = datetime.date.today()
            db.session.add(attendance_record)
            db.session.commit()
        else:
            return "Attendance already registered"

    return "Attendance registered"
