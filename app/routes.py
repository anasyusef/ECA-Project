from app import app, emails
from app.models import User, Role, Eca, Datetime, Registration, Attendance, WaitingList
from flask import render_template, redirect, url_for, flash, request, get_flashed_messages, session, abort
from app.forms import LoginForm, SignUpForm, EmailResetPassword, ResetPassword, AddEca, JoinEca, EditEca, \
    NotificationEca
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.decorators import permission_required, check_user_confirmed
import json
import datetime
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

    return redirect('login')


@app.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirm(token):
        flash('Your account is now confirmed! Thank you', 'success')
        db.session.commit()  # db.session.add() is already done on current_user.confirm(token)
        return redirect(url_for('index'))
    elif current_user.is_authenticated and not current_user.confirm(token):
        logout_user()
        flash('Please login with the appropriate user in order to confirm your account')
    elif current_user.confirmed:
        flash('Your account is already confirmed', 'error')
        redirect(url_for('index'))
    else:
        flash('Link is invalid or expired', 'error')

    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    #  In case the user went to /login by mistake or for some other reason, this piece of code is to ensure that
    #  when that happens, the page will redirect them to the right page.
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    #  End piece of code
    if form.validate_on_submit():
        q = User.query.filter_by(username=form.username.data).first()
        if q is not None and q.check_password(form.password.data):  # User found on the database and password is valid
            login_user(q, remember=form.remember_me.data)  # User Login
            next_url = request.args.get('next')
            return redirect(next_url or url_for('index'))
        else:
            flash('Invalid password or username', 'error')

    return render_template('login.html', form=form, title='ECA Project')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('index'))
    return render_template('unconfirmed.html')


@app.route('/resend_email')
def resend_email():
    if current_user.is_authenticated:
        token = current_user.generate_confirmation()
        emails.send_email(subject='Confirm your Account', recipients=[current_user.email],
                          html_body='auth/confirmation_email',
                          token=token, user=current_user)
        flash('An email has been sent to {}'.format(current_user.email), 'success')
        return redirect(url_for('index'))
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = SignUpForm()
    if form.validate_on_submit():
        #  Student information except password being prepared to be added to the database
        student = User(username=(form.student_username.data.lower()), first_name=form.student_first_name.data,
                       last_name=form.student_last_name.data,
                       email=form.student_email.data, role=Role.query.filter_by(name="Student").first())
        #  Student password being hashed with salt being prepared to be added to the database
        student.set_password(form.student_password.data)
        #  Student information being added to the session of the database
        db.session.add(student)
        # Database session is committed. Therefore, student information is now on the database
        db.session.commit()
        # Student has unconfirmed email. Therefore, a token has been generated for the user to confirm his email
        token = student.generate_confirmation()
        #  Token is sent to the user's email
        emails.send_email(subject='Confirm your Account', recipients=[student.email],
                          html_body='auth/confirmation_email',
                          token=token, user=student)
        flash('You have been successfully registered! Please check your email to confirm your account', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Add Student', form=form,
                           messages=get_flashed_messages(with_categories=True))


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = EmailResetPassword()
    if form.validate_on_submit():
        q = User.query.filter_by(email=form.email.data).first()
        if q is not None:
            token = q.generate_password_token(expiration=1300)
            emails.send_email(subject='Reset Password', recipients=[form.email.data],
                              html_body='auth/reset_password_email',
                              token=token, user=q)
        flash('Check your email for the instructions to reset your password', 'success')
        return redirect(url_for('index'))
    return render_template('reset_password.html', form=form, title='Reset Password')


@app.route('/reset_password_request/<token>', methods=['GET', 'POST'])
def reset_password_request(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    q = User.confirm_password_token(token)
    form = ResetPassword()
    if not q:
        flash('Link is invalid or expired', 'error')
        return redirect(url_for('index'))
    if form.validate_on_submit():
        q.count_password_request = 1
        q.set_password(form.password.data)
        db.session.add(q)
        db.session.commit()
        flash('Your password has been successfully changed!', 'success')
        return redirect(url_for('index'))
    return render_template('reset_password_request.html', form=form, title='Change Password')


@app.route('/add_eca', methods=['GET', 'POST'])
@login_required
@permission_required('Teacher')
def add_eca():
    form = AddEca()
    if form.validate_on_submit():
        if form.day_eca.data in [i.datetime.day for i in Eca.query.filter_by(user=current_user).all()]:
            flash('You cannot have two ECAs in the same day', 'error')
            return redirect(url_for('add_eca'))
        eca = Eca(name=form.eca_name.data, max_people=form.max_people.data,
                  max_waiting_list=form.max_waiting_list.data, location=form.location_eca.data)
        # Following line checks if there is an existing record that has the same time and same day that the user entered
        # this is to avoid data duplication in the database
        eca_time = Datetime.query.filter_by(day=form.day_eca.data, start_time=form.start_time_eca.data,
                                            end_time=form.end_time_eca.data).first()
        if bool(eca_time):  # If the query returns something means that there is an existing record
            eca.datetime = eca_time   # Therefore the new eca will point to the existing one
        else:
            eca.datetime = Datetime(day=form.day_eca.data, start_time=form.start_time_eca.data,
                                    end_time=form.end_time_eca.data)  # Otherwise it will create a new
            #  record
        eca.user = current_user
        eca.essentials = form.essentials_eca.data
        eca.brief_description = form.brief_description_eca.data
        db.session.add(eca)
        db.session.commit()

        flash('{} ECA has been added successfully!'.format(form.eca_name.data), 'success')

    return render_template('add_eca.html', form=form)


@app.route('/join_eca', methods=['GET', 'POST'])
@login_required
@permission_required('Student')
def join_eca():
    form = JoinEca()
    ecas = Eca.query.all()
    form.eca_name.choices = [(eca.name.lower(), eca.name) for eca in ecas]
    form.eca_name.choices.insert(0, ('choose', 'Choose...'))
    if form.validate_on_submit():

        # Make sure that the registration is duplicated. To ensure this, a query needs to be run. If the query
        # does not return any value means that there is no registration from the user to the specific ECA
        eca = Eca.query.filter_by(name=form.eca_name.data).first()
        if validate_user_data_registration(eca):
            # Registration is needed even if the eca has reached its maximum capacity because it will be used for the
            # waiting list
            if len(eca.registration) == eca.max_people:
                db.session.add(WaitingList(user=current_user, eca=eca))
                try:
                    db.session.commit()
                    flash('This ECA has reached its maximum capacity of students, you will be put on the waiting list',
                          'error')
                except IntegrityError:
                    flash('You have been already added into the waiting list of this ECA', 'error')
                    db.session.rollback()
                    return redirect(url_for('join_eca'))
            else:
                registration = Registration(user=current_user, eca=eca)
                db.session.add(registration)
                db.session.commit()
                flash('You have joined into {} successfully!'.format(eca.name), 'success')
    return render_template('join_eca.html', form=form, ecas=ecas)


def validate_user_data_registration(eca):
    query_check = Registration.query.filter_by(user=current_user, eca=eca).first()
    all_registrations_by_user = Registration.query.filter_by(user=current_user).all()
    if query_check is not None:
        flash('You cannot register for the same ECA twice', 'error')
        return False

    for registration in all_registrations_by_user:
        if registration.eca.datetime.day == eca.datetime.day:  # Checks if any of the ECA's day matches with the ones
            # that are already registered. If there are, then a warning will be shown to the user
            flash('You cannot register in more than one ECA in the same day')
            return False

    return True


@app.route('/eca_info')
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


@app.route('/edit_eca')
@login_required
@permission_required('Teacher')
def edit_eca():
    ecas = Eca.query.filter_by(user=current_user).all()
    return render_template('edit_eca_dashboard.html', ecas=ecas)


@app.route('/eca/update/<eca_name>', methods=['GET', 'POST'])
@login_required
@permission_required('Teacher')
def eca_name_edit(eca_name):
    eca_names = [eca_name.name.lower() for eca_name in Eca.query.filter_by().all()]
    if eca_name.lower() not in eca_names:
        return "ECA Not Found", 404
    form = EditEca()
    eca = Eca.query.filter_by(name=eca_name).first()
    if eca.user != current_user:
        flash('You are not allowed to edit this ECA', 'error')
        return redirect('edit_eca')
    # Time is converted to string in order to avoid errors while rendering the template and passing it as a value
    # to a field
    start_time_eca = eca.datetime.start_time.strftime('%H:%M')
    end_time_eca = eca.datetime.end_time.strftime('%H:%M')

    if form.validate_on_submit():

        # The following code checks if the day has been updated (changed), if it has it checks if the day of the ECA
        # has already been chosen for another ECA by the same user, if it has then it throws an error saying that
        # 'You cannot have two ECAs in the same day'
        if not form.day_eca.data == eca.datetime.day:
            if form.day_eca.data in [i.datetime.day for i in Eca.query.filter_by(user=current_user).all()]:
                flash('You cannot have two ECAs in the same day', 'error')
                return redirect(url_for('eca_name_edit', eca_name=eca_name))
        eca.name = form.eca_name.data
        eca.max_people = form.max_people.data
        eca.max_waiting_list = form.max_waiting_list.data
        eca.datetime.day = form.day_eca.data
        eca.essentials = form.essentials_eca.data
        eca.datetime.start_time = form.start_time_eca.data if form.start_time_eca.data else eca.datetime.start_time
        eca.datetime.end_time = form.end_time_eca.data if form.end_time_eca.data else eca.datetime.end_time
        db.session.add(eca)
        db.session.commit()
        flash("ECA has been updated successfully", "success")
        return redirect(url_for('edit_eca'))
    return render_template('edit_eca.html', eca_name=eca_name, form=form, eca=eca, start_time_eca=start_time_eca,
                           end_time_eca=end_time_eca)


@app.route('/eca/delete/<eca_name>')
@login_required
@permission_required('Teacher')
def delete_eca(eca_name):
    db.session.rollback()
    eca_to_delete = Eca.query.filter_by(name=eca_name)

    if eca_to_delete is None:
        return "ECA Not Found", 404

    if eca_to_delete.first().user != current_user:
        return "You cannot delete this ECA", 403

    # Get the emails of the students related to the eca removed
    if len(eca_to_delete.first().registration) > 0:  # Ensures that there are users registered in the ECA
        users_related_to_ecas = [recipient.user for recipient in
                                 Registration.query.filter_by(eca=eca_to_delete.first())]
        emails.send_email(subject='{} ECA has been removed'.format(eca_name.title()),
                          recipients=[user.email for user in users_related_to_ecas],
                          html_body='email_eca_removed', users=users_related_to_ecas, eca_name=eca_name.title())
        Registration.query.filter_by(eca=eca_to_delete.first()).delete()
    eca_to_delete.delete()
    db.session.commit()
    flash('ECA has been deleted successfully', 'success')
    return redirect(url_for('edit_eca'))


@app.route('/eca/quit/<eca_name>/')
@login_required
@permission_required('Student')
def quit_eca(eca_name):
    eca = Eca.query.filter_by(name=eca_name).first()
    Registration.query.filter_by(user=current_user, eca=eca).delete()
    db.session.commit()
    flash('You have quit the {} ECA successfully!'.format(eca.name), 'success')
    return redirect(url_for('attendance_eca'))


@app.route('/eca/delete_student/<eca_name>/')
@login_required
@permission_required('Teacher')
def delete_student(eca_name):
        user_to_delete = User.query.filter_by(id=request.args.get('id')).first()
        eca_user_related = Eca.query.filter_by(name=eca_name).first()
        # TODO restrict access so only authorised users have access to this route
        if request.args.get('action') is not None:
            if request.args.get('action') == 'remove':
                user_registration = Registration.query.filter_by(user=user_to_delete, eca=eca_user_related)
                user_registration.delete()
                db.session.commit()
                # TODO send email when a user is deleted from the ECA
                # Code to remove student from waiting list and add it to the registration list
                front_user_waiting_list = WaitingList.query.filter_by(eca=eca_user_related)
                if front_user_waiting_list.first() is not None:
                    new_user_registration = Registration(eca=eca_user_related,
                                                         user=front_user_waiting_list.first().user)
                    WaitingList.query.filter_by(eca=eca_user_related,
                                                user=front_user_waiting_list.first().user).delete()
                    # TODO send email when the user is removed from the waiting list
                    db.session.add(new_user_registration)
                    db.session.commit()
            elif request.args.get('action') == 'remove_wl':
                user_waiting_list = WaitingList.query.filter_by(user=user_to_delete, eca=eca_user_related)
                user_waiting_list.delete()
                db.session.commit()

        return 'Student Removed'


@app.route('/attendance_eca')
@login_required
def attendance_eca():

    if current_user.role.name.lower() == 'teacher':
        ecas = Eca.query.filter_by(user=current_user).all()
    else:
        ecas = [student_eca.eca for student_eca in Registration.query.filter_by(user=current_user).all()]
        # Takes all the ecas that the current user is registered to

    return render_template('base_ecas_overview.html', ecas=ecas, current_user=current_user)


@app.route('/eca/take_attendance/<eca_name>')
@login_required
@permission_required('Teacher')
def take_attendance(eca_name):
    eca = Eca.query.filter_by(name=eca_name).first()

    if eca is None:
        return "ECA Not Found", 404

    if eca.user != current_user:
        flash("You are not allowed to take attendance on this ECA", "error")
        return redirect(url_for('attendance_eca'))

    if eca.datetime.day != datetime.date.today().strftime('%A').lower():
        flash('You cannot take attendance since the ECA is not taking place today', 'error')
        return redirect(url_for('attendance_eca'))
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
                    flash('You are not allowed to go to this page', 'error')
                    return redirect(url_for('attendance_eca'))
            return render_template('view_attendance_detail.html',
                                   attendance_info=Attendance.query.filter_by(registration=registration_user)
                                   .order_by(desc(Attendance.date)), eca=eca, user=user)
        else:
            if current_user.role.name.lower() == 'teacher':  # This is done for security purposes, so that students
                # cannot see who is in an ECA and who is not
                flash('This user is not in this ECA' if current_user.role.name.lower() == 'teacher'
                      else 'You are not allowed to go to this page', 'error')

            return redirect(url_for('attendance_eca'))
    if eca is None:
        return "ECA Not Found", 404

    if eca.user != current_user:
        flash("You are not allowed to view attendance on this ECA", "error")
        return redirect(url_for('attendance_eca'))

    return render_template('view_attendance.html', Attendance=Attendance, eca=eca)


@app.route('/view_attendance_detail/<eca_name>/<user_id>')
def view_attendance_detail_api(eca_name, user_id):
    # TODO only allow user registered on the website (Restrict Access)
    eca = Eca.query.filter_by(name=eca_name).first()
    user = User.query.filter_by(id=user_id).first()
    if eca_name.lower() == 'overall':
        registration_user = Registration.query.filter_by(user=user).first()
        user_attendance_true = len(Attendance.query.filter_by(registration=registration_user, attended=True).all())
        user_attendance_false = len(Attendance.query.filter_by(registration=registration_user, attended=False).all())
        user_attendance_total = len(Attendance.query.filter_by(registration=registration_user).all())
    else:
        registration_user = Registration.query.filter_by(user=user, eca=eca).first()
        user_attendance_true = len(Attendance.query.filter_by(registration=registration_user, attended=True).all())
        user_attendance_false = len(Attendance.query.filter_by(registration=registration_user, attended=False).all())
        user_attendance_total = len(Attendance.query.filter_by(registration=registration_user).all())
    return json.dumps({'attendance_true': user_attendance_true, 'attendance_false': user_attendance_false,
                       'attendance_total': user_attendance_total,
                       'percentage_attendance_true':
                           (user_attendance_true/(user_attendance_total if user_attendance_total != 0 else 1)) * 100,
                       'percentage_attendance_false':
                           (user_attendance_false/(user_attendance_total if user_attendance_total != 0 else 1)) * 100})


@app.route('/notification_eca', methods=['GET', 'POST'])
@login_required
@permission_required('Teacher')
def notification_eca():
    form = NotificationEca()
    ecas = Eca.query.filter_by(user=current_user).all()
    form.eca_name.choices = [(eca.name.lower(), eca.name) for eca in ecas]
    form.eca_name.choices.insert(0, ('choose', 'Choose...'))
    form.status_notification.choices = [('postponed', 'Postponed'), ('cancelled', 'Cancelled')]
    form.status_notification.choices.insert(0, ('choose', 'Choose...'))
    form.status_notification.choices.append(('custom', 'Custom'))
    reason_variables = [('{user_first_name}', 'User first name'), ('{user_last_name}', 'User last name'),
                        ('{eca_name}', 'ECA name')]
    variables = [variable for variable, reason in reason_variables]
    if form.validate_on_submit():
        eca = Eca.query.filter_by(name=form.eca_name.data).first()
        action = form.status_notification.data if form.status_notification.data != 'custom' \
            else form.custom_status_notification.data
        email_subject = '{} - {}'.format(form.eca_name.data.title(), action.title())
        users_related_to_eca = [user.user for user in eca.registration]
        recipients = [user.email for user in users_related_to_eca]

        emails.send_email(subject=email_subject, recipients=recipients, html_body='email_notification_eca',
                          users=users_related_to_eca, eca_name=eca.name.title(), reason=form.reason.data,
                          action=action.title())

        flash('Your notification has been sent successfully!', 'success')

    return render_template('eca_notification.html', form=form, reason_variables=reason_variables)
