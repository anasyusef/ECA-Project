import re

from flask import flash, request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, InputRequired
from wtforms_components import TimeField

from app.emails import send_email
from app.models import User, Eca, Registration, db


class LoginForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class SignUpForm(FlaskForm):

    student_username = StringField('Username', validators=[DataRequired(), Length(min=2, max=25)])
    student_password = PasswordField('Password', validators=[DataRequired()])
    student_first_name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=25)])
    student_last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=25)])
    student_email = StringField("Email", validators=[DataRequired(), Email(), Length(min=4, max=50)])
    student_confirm_email = StringField("Confirm Email",
                                        validators=[DataRequired(), EqualTo('student_email',
                                                                            message="Email Address must match")])

    def validate_student_email(self, email):
        query = User.query.filter_by(email=email.data).first()
        if query is not None:
            flash('Email Address already exist. Please use a different one.', 'danger')
            raise ValidationError('Email Address already exist. Please use a different one.')

    def validate_student_username(self, username):
        query = User.query.filter_by(username=username.data).first()
        if query is not None:
            flash('Username already exist. Please use a different one.', 'danger')
            raise ValidationError('Username already exist. Please use a different one.')


class EmailResetPassword(FlaskForm):

    email = StringField('Email Address', validators=[DataRequired()])


class EmailForgotUsername(FlaskForm):

    email = StringField('Email Address', validators=[DataRequired()])


class ResetPassword(FlaskForm):

    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])


class AddEca(FlaskForm):

    eca_name = StringField('ECA Name', validators=[DataRequired()])
    max_people = IntegerField('Maximum Capacity (Students)', validators=[DataRequired()])
    max_waiting_list = IntegerField('Waiting List', validators=[InputRequired()])
    start_time_eca = TimeField('Start Time', validators=[DataRequired()])
    end_time_eca = TimeField('End Time', validators=[DataRequired()])
    day_eca = SelectField('Day', choices=[('monday', 'Monday'), ('tuesday', 'Tuesday'),
                                                            ('wednesday', 'Wednesday'), ('thursday', 'Thursday'),
                                                            ('friday', 'Friday'), ('saturday', 'Saturday'),
                                          ('sunday', 'Sunday')])
    location_eca = StringField('Location', validators=[DataRequired()])
    essentials_eca = TextAreaField('Essentials (Optional)')
    brief_description_eca = StringField('Brief Description (Optional)')

    def validate_eca_name(self, name):
        characters_not_valid = ('/', '&')
        query = Eca.query.filter_by(name=name.data).first()
        if query is not None:
            raise ValidationError('ECA already exists. Please create a different one.')

        pattern_not_accepted = re.compile('[&/]+')
        if bool(pattern_not_accepted.findall(name.data)) is True:
            raise ValidationError("The following characters are not valid: {} ".
                                  format(characters_not_valid))

    def validate_end_time_eca(self, end_time):
        if end_time.data <= self.start_time_eca.data:
            raise ValidationError("{} field cannot be earlier or equal than {} field"
                                  .format(self.end_time_eca.label.text, self.start_time_eca.label.text))


class JoinEca(FlaskForm):

    eca_name = SelectField('ECA Name', validators=[DataRequired()])

    def validate_eca_name(self, eca):

        # Validation if user chooses 'choose' as an option

        if eca.data == 'choose':
            raise ValidationError('Please choose an ECA')

        eca = Eca.query.filter_by(name=eca.data).first()
        query_check = Registration.query.filter_by(user=current_user, eca=eca).first()
        all_registrations_by_user = Registration.query.filter_by(user=current_user).all()
        all_registrations_in_eca = Registration.query.filter_by(eca=eca).all()

        # Validation if the student is already registered in one ECA and is trying to register in the same one

        if query_check is not None:
            flash('You cannot register for the same ECA twice', 'danger')
            raise ValidationError()

        # Validation if the student is registered in more than one ECA in the same day

        for registration in all_registrations_by_user:
            if registration.eca.datetime.day == eca.datetime.day:  # Checks if any of the ECA's day matches
                # with the ones
                # that are already registered. If there are, then a warning will be shown to the user
                flash('You cannot register in more than one ECA in the same day', 'danger')
                raise ValidationError()

        # Validation if student is trying to register and the capacity of active members is reached and the capacity
        # of the waiting list is reached or there is no waiting list

        if eca.max_waiting_list == 0 and len(all_registrations_in_eca) == eca.max_people:
            flash('This ECA has no waiting list and therefore if you want to join into this ECA, you'
                  ' will need to wait until some student drops out or is removed from the ECA', 'info')
            raise ValidationError()

        elif len(Registration.query.filter_by(eca=eca, in_waiting_list=True).all()) == eca.max_waiting_list and \
                len(all_registrations_in_eca) == eca.max_people:
            flash('This ECA has reached its waiting list capacity, if you still want to join into this'
                  ' ECA you will need to wait until some student drops out or is removed from the ECA',
                  'info')
            raise ValidationError()

        # Validation to make sure that the student can only join in an active ECA

        if not eca.is_active:
            flash('You have joined into an ECA that is not active, therefore it will not be taking place until'
                  ' the organiser makes the ECA active again.', 'warning')


class EditEca(AddEca, FlaskForm):

    status_eca = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Inactive')])

    def validate_eca_name(self, name):
        characters_not_valid = ('/', '&')
        eca_name = request.path.split('/')[-1]
        if name.data.lower() != eca_name.lower():
            query = Eca.query.filter_by(name=name.data).first()
            if query is not None:
                raise ValidationError('ECA already exists. Please choose a different one.')

        pattern_not_accepted = re.compile('[&/]+')
        if bool(pattern_not_accepted.findall(name.data)) is True:
            raise ValidationError("The following characters are not valid: {} ".
                                  format(characters_not_valid))

    def validate_max_people(self, max_people):
        eca = Eca.query.filter_by(name=request.path.split('/')[-1]).first()
        if max_people.data < len(Registration.query.filter_by(eca=eca).all()):
            raise ValidationError('You need to remove students already joined in order to decrease the capacity of'
                                  ' students allowed')

    def validate_max_waiting_list(self, max_waiting_list):
        eca = Eca.query.filter_by(name=request.path.split('/')[-1]).first()
        if max_waiting_list.data < len(Registration.query.filter_by(eca=eca, in_waiting_list=True).all()):
            raise ValidationError('You need to remove students already joined in the waiting list in order '
                                  'to decrease the capacity of students in the waiting list allowed')


class NotificationEca(FlaskForm):
    eca_name = SelectField('ECA Name', validators=[DataRequired()])
    status_notification = SelectField('Status')
    custom_status_notification = StringField('Custom')
    reason = TextAreaField('Reason', validators=[DataRequired()])

    def validate_status_notification(self, choice):
        if choice.data == 'choose':
            raise ValidationError('Please choose something')

    def validate_eca_name(self, choice):
        if choice.data == 'choose':
            raise ValidationError('Please choose something')

    def validate_custom_status_notification(self, choice):
        if choice.data == "" and self.status_notification.data == "custom":
            raise ValidationError('Please enter something')


class SortBy(FlaskForm):

    sort_by = SelectField('Sort by', choices=[('first_name', 'First Name'), ('last_name', 'Last Name'),
                                              ('highest_attendance', 'Highest Attendance'),
                                              ('lowest_attendance', 'Lowest Attendance')])


class UpdateProfile(FlaskForm):

    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    old_password = PasswordField('Old Password')
    new_password = PasswordField('New Password')
    confirm_password = PasswordField('Confirm Password',validators=[EqualTo('new_password',
                                                                            message='Passwords do not match')])

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        if self.username.data != current_user.username:
            current_user.username = self.username.data
            db.session.add(current_user)
            db.session.commit()

        if current_user.check_password(self.new_password.data):  # Condition to check if the password in the
            # 'New Password' field is the same as the current password of the user
            flash('New password cannot be the same as the old one', 'danger')
            return False  # Returns False since it means that the validation has failed
        if bool(self.old_password.data) is not False:  # Condition to check if the user has entered some data
            # on the 'Old Password field', if he/she has then an extra validator is added to the 'New Password' field
            # which is to make the field required
            self.new_password.validate(self,
                                       extra_validators=[DataRequired(message='Please enter new password')])
            # If the extra validation has passed then the new password of the user is set
            current_user.set_password(self.new_password.data)
            # The current user is added to the session of the database
            db.session.add(current_user)
            # Any changes to the database are being saved
            db.session.commit()
        return True  # Returns True since it means that the validation has passed

    def validate_username(self, username):

            if username.data.lower() != current_user.username.lower():  # Checks if the username entered is the same
                # as the current username, if it is not, then the following code is executed
                if User.query.filter_by(username=username.data.lower()).first() is not None:  # If the query returns a
                    # value, which means that the username entered by the user already exists.
                    raise ValidationError('Username already exists. Please choose a different one')

    def validate_email(self, email):
        if email.data.lower() != current_user.email.lower():
            if User.query.filter_by(email=email.data.lower()).first() is not None:
                raise ValidationError('Email already in use. Please choose a different one')
            else:
                token = current_user.generate_confirmation_change_email(current_user.email, self.email.data)
                #  Token is sent to the user's email
                send_email(subject='Confirm your Account', recipients=[self.email.data],
                           html_body='auth/confirmation_email',
                           token=token, user=current_user, change_email=True)
                flash('An email verification has been sent to the new email address, please click the link sent to'
                      ' successfully change it',
                      'info')

    def validate_old_password(self, old_password):

        if bool(old_password.data) is not False or bool(self.new_password.data) is not False:
            if not current_user.check_password(old_password.data):
                raise ValidationError('Old password is incorrect')
