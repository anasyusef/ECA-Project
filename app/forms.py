from flask import flash, request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, InputRequired
from wtforms_components import TimeField

from app.models import User, Eca, Registration, WaitingList


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

        for character in characters_not_valid:
            if character in name.data:
                raise ValidationError("The following characters are not valid: {} ".format(characters_not_valid))

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

        # Validation if the student is already registered in one ECA and is trying to register in the same one

        if query_check is not None:
            flash('You cannot register for the same ECA twice', 'danger')
            raise ValidationError()

        # Validation if the student is registered in more than one ECA in the same day

        for registration in all_registrations_by_user:
            print(registration)
            if registration.eca.datetime.day == eca.datetime.day:  # Checks if any of the ECA's day matches
                # with the ones
                # that are already registered. If there are, then a warning will be shown to the user
                flash('You cannot register in more than one ECA in the same day', 'danger')
                raise ValidationError()

        # Validation if student is trying to register and the capacity of active members is reached and the capacity
        # of the waiting list is reached or there is no waiting list

        if eca.max_waiting_list == 0:
            flash('This ECA has no waiting list and therefore if you want to join into this ECA, you'
                  ' will need to wait until some student drops out or is removed from the ECA', 'info')
            raise ValidationError()

        elif len(WaitingList.query.filter_by(eca=eca).all()) == eca.max_waiting_list:
            flash('This ECA has reached its waiting list capacity, if you still want to join into this'
                  ' ECA you will nee to wait until some student drops out or is removed from the ECA',
                  'info')
            raise ValidationError()

        # Validation to make sure that the student can only join in an active ECA

        if not eca.is_active:
            flash('You have joined into an ECA that is not active, therefore the ECA will need to wait until'
                  ' will not be taking place until the organiser makes the ECA active again', 'warning')


class EditEca(AddEca, FlaskForm):

    status_eca = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Inactive')])

    def validate_eca_name(self, name):
        characters_not_valid = ('/', '&')
        for character in characters_not_valid:
            if character in name.data:
                raise ValidationError("The following characters are not valid: {} ".format(characters_not_valid))

    def validate_max_people(self, max_people):
        eca = Eca.query.filter_by(name=request.path.split('/')[-1]).first()
        if max_people.data < len(Registration.query.filter_by(eca=eca).all()):
            raise ValidationError('You need to remove students already joined in order to decrease the capacity of'
                                  ' students allowed')

    def validate_max_waiting_list(self, max_waiting_list):
        eca = Eca.query.filter_by(name=request.path.split('/')[-1]).first()
        if max_waiting_list.data < len(WaitingList.query.filter_by(eca=eca).all()):
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

    student_username = StringField('Username', validators=[DataRequired(), Length(min=2, max=25)])
    student_email = StringField('Email', validators=[DataRequired(), Email()])
    student_old_password = PasswordField('Old Password')
    student_new_password = PasswordField('New Password')
    student_confirm_password = PasswordField('Confirm Password',
                                             validators=[EqualTo('student_new_password',
                                                                 message='Passwords do not match')])

    def validate_student_username(self, username):

        if username.data != current_user.username:
            if User.query.filter_by(username=username.data).first() is not None:
                raise ValidationError('Username already exists. Please choose a different one')

    def validate_student_email(self, email):

        if email.data != current_user.email:
            if User.query.filter_by(email=email.data).first() is not None:
                raise ValidationError('Email already in use. Please choose a different one')

    def validate_student_old_password(self, old_password):
        if bool(old_password.data) is not False or bool(self.student_new_password.data) is not False:
            if not current_user.check_password(old_password.data):
                raise ValidationError('Old password is incorrect')
