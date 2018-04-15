from flask import redirect, url_for, render_template, get_flashed_messages
from flask_login import login_user, logout_user, login_required

from app.auth import bp
from app.emails import send_email
from app.forms import *
from app.models import *
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])
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
            flash('Invalid password or username', 'danger')

    return render_template('login.html', form=form, title='ECA Project')


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = SignUpForm()
    if form.validate_on_submit():
        #  Student information except password being prepared to be added to the database
        student = User()
        student.username = form.student_username.data.lower()
        student.first_name = form.student_first_name.data
        student.last_name = form.student_last_name.data
        student.email = form.student_email.data
        student.role = Role.query.filter_by(name="Student").first()
        #  Student password being hashed with salt being prepared to be added to the database
        student.set_password(form.student_password.data)
        #  Student information being added to the session of the database
        db.session.add(student)
        # Database session is committed. Therefore, student information is now on the database
        db.session.commit()
        # Student has unconfirmed email. Therefore, a token has been generated for the user to confirm his email
        token = student.generate_confirmation()
        #  Token is sent to the user's email
        send_email(subject='Confirm your Account', recipients=[student.email],
                   html_body='auth/confirmation_email',
                   token=token, user=student)
        flash('You have been successfully registered! Please check your email to confirm your account', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', title='Add Student', form=form,
                           messages=get_flashed_messages(with_categories=True))


@bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = EmailResetPassword()
    if form.validate_on_submit():
        q = User.query.filter_by(email=form.email.data).first()
        if q is not None:
            token = q.generate_password_token(expiration=1300)
            send_email(subject='Reset Password', recipients=[form.email.data],
                       html_body='auth/reset_password_email', token=token, user=q)
        flash('Check your email for the instructions to reset your password', 'success')
        return redirect(url_for('index'))
    return render_template('reset_password.html', form=form, title='Reset Password')


@bp.route('/reset_password_request/<token>', methods=['GET', 'POST'])
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


@bp.route('/confirm/<token>')
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


@bp.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('index'))
    return render_template('unconfirmed.html', title='Unconfirmed Account')


@bp.route('/resend_email')
def resend_email():
    if current_user.is_authenticated:
        token = current_user.generate_confirmation()
        send_email(subject='Confirm your Account', recipients=[current_user.email],
                   html_body='auth/confirmation_email', token=token, user=current_user)
        flash('An email has been sent to {}'.format(current_user.email), 'success')
        return redirect(url_for('index'))
    return redirect(url_for('index'))


@bp.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    if current_user.is_authenticated:
        form = UpdateProfile()

        if form.validate_on_submit():
            # Extra validators
            if form.student_username.data != current_user.username:
                current_user.username = form.student_username.data
                db.session.add(current_user)
                db.session.commit()
            if current_user.check_password(form.student_new_password.data):
                flash('New password cannot be the same as the old one', 'danger')
                return redirect(url_for('auth.user_profile'))
            # If the user has entered some data in the old password field, then the new password field must not be empty
            # Therefore the following condition is to solve this issue
            if bool(form.student_old_password.data) is not False:
                form.student_new_password.validate(form,
                                                   extra_validators=[DataRequired(message='Please enter new password')])
                # If the new message has not been shown, then everything went fine and the password is going
                # to be changed The following condition checks that there are no errors in
                # the new password field and if there is not then the password is going to be changed
                if bool(form.student_new_password.errors) is False:
                    current_user.set_password(form.student_new_password.data)
                    db.session.add(current_user)
                    db.session.commit()

            # The inline if statement ensures that the notification is shown only when there is no error on the
            # new password field, it only checks this field since all other fields have been handled properly when
            # an error is triggered and because we have put extra validators on the new password field, which is when
            # the old password field has some data, the extra validator is triggered.
            flash('Changes have been saved!', 'success') if bool(form.student_new_password.errors) is False else None

        return render_template('user_profile.html', current_user=current_user, form=form, title='Update Profile')
    return redirect(url_for('index'))
