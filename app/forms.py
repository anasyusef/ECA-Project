from flask_wtf import FlaskForm
from flask import flash, request
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, SelectField, TextAreaField
from wtforms_components import TimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, InputRequired
from app.models import User, Eca
import datetime


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
    student_email = StringField("Email", validators=[DataRequired(), Email(), Length(min=4, max=40)])
    student_confirm_email = StringField("Confirm Email",
                                        validators=[DataRequired(), EqualTo('student_email',
                                                                            message="Email Address must match")])

    def validate_student_email(self, email):
        query = User.query.filter_by(email=email.data).first()
        if query is not None:
            flash('Email Address already exist. Please use a different one.', 'error')
            raise ValidationError('Email Address already exist. Please use a different one.')

    def validate_student_username(self, username):
        query = User.query.filter_by(username=username.data).first()
        if query is not None:
            flash('Username already exist. Please use a different one.', 'error')
            raise ValidationError('Username already exist. Please use a different one.')


class EmailResetPassword(FlaskForm):

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

    def validate_eca_name(self, name):
        if name.data == 'choose':
            raise ValidationError('Please choose an ECA')


class EditEca(AddEca, FlaskForm):

    def validate_eca_name(self, name):
        characters_not_valid = ('/', '&')
        for character in characters_not_valid:
            if character in name.data:
                raise ValidationError("The following characters are not valid: {} ".format(characters_not_valid))


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
