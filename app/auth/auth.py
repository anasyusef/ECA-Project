from flask import redirect, url_for, render_template, get_flashed_messages
from flask_login import login_user, logout_user, login_required

from app.auth import bp
from app.decorators import check_user_confirmed
from app.forms import *
from app.models import *
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])  # Test plan complete
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


@bp.route('/register', methods=['GET', 'POST'])  # Test plan complete
def register():
    form = SignUpForm()
    if form.validate_on_submit():
        #  Student information except password being prepared to be added to the database
        student = User()  # Instantiate an object from the User class, which means that a record is going to be added
        # to the users table
        student.username = form.student_username.data.lower() # It assigns the username of the student and it makes
        # sure that is in lowercase to avoid case-sensitivity. This is done with the lower() method
        student.first_name = form.student_first_name.data
        student.last_name = form.student_last_name.data
        student.email = form.student_email.data
        student.role = Role.query.filter_by(name="Student").first()  # It looks for the Student role in the database
        # and it assigns that role to the user registering on the website
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


@bp.route('/reset_password', methods=['GET', 'POST'])  # Test plan complete
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = EmailResetPassword()
    if form.validate_on_submit():
        q = User.query.filter_by(email=form.email.data).first()
        if q is not None:
            token = q.generate_password_token(expiration=3600)
            send_email(subject='Reset Password', recipients=[form.email.data],
                       html_body='auth/reset_password_email', token=token, user=q)
        flash('Check your email for the instructions to reset your password', 'success')
        return redirect(url_for('index'))
    return render_template('forgot_credentials.html', form=form, title='Forgot Password')


@bp.route('/forgot_username', methods=['GET', 'POST'])  # Test plan complete
def forgot_username():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = EmailForgotUsername()
    if form.validate_on_submit():
        q = User.query.filter_by(email=form.email.data).first()
        if q is not None:
            send_email(subject='Username Reminder', recipients=[form.email.data],
                       html_body='auth/forgot_username_email', user=q)
        flash('The username has been sent to your email', 'success')
        return redirect(url_for('index'))
    return render_template('forgot_credentials.html', form=form, title='Forgot Username')


@bp.route('/reset_password_request/<token>', methods=['GET', 'POST'])
def reset_password_request(token):  # Test plan complete
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    q = User.confirm_password_token(token)  # id of the user requesting to change the password is gotten from the
    #  confirm_password_token() method, since the id of the user is encrypted on the token that was sent through
    # the email
    form = ResetPassword()
    if not q:
        flash('Link is invalid or expired', 'danger')
        return redirect(url_for('index'))
    if form.validate_on_submit():
        q.set_password(form.password.data)  # form.password.data is the value of the password field, so this method
        # hashes the new password entered by the user and assigns it to the password_hash field on the database for the
        # appropiate user
        db.session.add(q)  # To add the new updated user to the session to the database
        db.session.commit()  # To save changes made on the database
        flash('Your password has been successfully changed!', 'success')
        return redirect(url_for('index'))
    return render_template('reset_password_request.html', form=form, title='Change Password')


@bp.route('/confirm/<token>')  # Test plan complete
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
        flash('Your account is already confirmed', 'danger')
        redirect(url_for('index'))
    else:
        flash('Link is invalid or expired', 'danger')

    return redirect(url_for('index'))


@bp.route('/change_email/<token>')
def change_email(token):
    valid, new_email = current_user.confirm_change_email(token)
    if valid:
        flash('Your email has been successfully changed!', 'success')
        db.session.commit()
        return redirect(url_for('auth.user_profile'))
    elif current_user.email == new_email:
        flash('Email already verified', 'info')
        return redirect(url_for('auth.user_profile'))
    elif not valid:
        flash('Link is invalid or expired, please request a new email', 'danger')
        db.session.rollback()
        return redirect(url_for('auth.user_profile'))


@bp.route('/unconfirmed')  # Test plan complete
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
@check_user_confirmed
def user_profile():
    if current_user.is_authenticated:
        form = UpdateProfile()

        if form.validate_on_submit():
            flash('Changes have been saved!', 'success') if not bool(form.errors) else None
        return render_template('user_profile.html', current_user=current_user, form=form, title='Update Profile')

    return redirect(url_for('index'))
