import datetime
import random
import re

import forgery_py
from flask_login import UserMixin, current_user
from jwt import encode, decode, DecodeError, ExpiredSignatureError
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login, app


class User(UserMixin, db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, index=True, nullable=False)
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(128), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False, nullable=False)
    role_id = db.Column('role_id', db.ForeignKey('roles.id'), nullable=False)
    eca = db.relationship('Eca', back_populates='user')
    role = db.relationship('Role', back_populates='user')
    registration = db.relationship('Registration', back_populates='user')

    def __repr__(self):
        return "<User {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation(self, expiration=3600):
        return encode({'confirm': self.id, 'exp': datetime.datetime.utcnow() +
                       datetime.timedelta(seconds=expiration)}, key=app.config['SECRET_KEY'], algorithm='HS256')

    def generate_confirmation_change_email(self, current_email, new_email, expiration=3600):
        return encode({'confirm': self.id, 'current_email': current_email, 'new_email': new_email,
                       'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration)},
                      key=app.config['SECRET_KEY'], algorithm='HS256')

    def generate_password_token(self, expiration=3600):
        return encode({'password_reset': self.id,
                       'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration)},
                      key=app.config['SECRET_KEY'], algorithm='HS256')

    def confirm(self, token):
        try:
            decoded = decode(token, key=app.config['SECRET_KEY'], algorithm='HS256')
        except (DecodeError, ExpiredSignatureError):
            return False
        if decoded.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def confirm_change_email(self, token):
        try:
            decoded = decode(token, key=app.config['SECRET_KEY'], algorithm='HS256')
        except (DecodeError, ExpiredSignatureError):
            return False, None
        if decoded.get('confirm') != self.id:
            return False, decoded.get('new_email')
        elif decoded.get('current_email') != current_user.email:
            return False, decoded.get('new_email')
        self.email = decoded.get('new_email')
        db.session.add(self)
        return True, decoded.get('new_email')

    @staticmethod
    def confirm_password_token(token):
        try:
            user_id = decode(token, key=app.config['SECRET_KEY'], algorithm='HS256').get('password_reset')
        except (DecodeError, ExpiredSignatureError):
            return False
        return User.query.get(user_id)

    @staticmethod
    def generate_fake(users, role):

        for i in range(users):
            user = User(username=forgery_py.internet.user_name(), first_name=forgery_py.name.first_name(),
                        last_name=forgery_py.name.last_name(), email=forgery_py.internet.email_address())
            user.password_hash = generate_password_hash('12345')
            user.confirmed = True
            user.role = Role.query.filter_by(name=role).first()
            if user.role is None:
                return "Please enter a correct role"
            else:
                db.session.add(user)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()

    @staticmethod
    def add_main_users():

        user_info = [('Anas Yousef', 'anasyusef@hotmail.com', 'Teacher'),
                     ('Student Test', 'termosad@hotmail.com', 'Student'),
                     ('Teacher Test', 'anasfreelancer2807@gmail.com', 'Teacher'),
                     ('Student1 Test', 'samenza2807@gmail.com', 'Student')]

        for user_full_name, email, role in user_info:
            user_first_name = user_full_name.split(' ')[0]
            user_last_name = user_full_name.split(' ')[1]
            user_username = user_first_name + '.' + user_last_name
            user = User(first_name=user_first_name, last_name=user_last_name, username=user_username, email=email)
            user.confirmed = True
            user.set_password('12345')
            user.role = Role.query.filter_by(name=role).first()
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class Role(db.Model):

    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), nullable=False, index=True)
    user = db.relationship('User', back_populates='role')

    @staticmethod
    def insert_roles():
        student_role = Role.query.filter_by(name='Student').first()
        teacher_role = Role.query.filter_by(name='Teacher').first()
        if student_role is not None or teacher_role is not None:
            try:
                Role.query.delete()
                try:
                    db.session.add_all([Role(name='Teacher'), Role(name='Student')])
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
            except IntegrityError:
                db.session.rollback()
        else:
            try:
                db.session.add_all([Role(name='Teacher'), Role(name='Student')])
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return "<Role {}>".format(self.name)


class Eca(db.Model):

    __tablename__ = 'ecas'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    max_people = db.Column(db.Integer)
    max_waiting_list = db.Column(db.Integer)
    location = db.Column(db.String(64), nullable=False)
    brief_description = db.Column(db.String(128))
    essentials = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column('user_id', db.ForeignKey('users.id'), nullable=False)
    datetime_id = db.Column('datetime_id', db.ForeignKey('datetimes.id'), nullable=False)
    datetime = db.relationship('Datetime', back_populates='eca')
    user = db.relationship('User', back_populates='eca')
    registration = db.relationship('Registration', back_populates='eca', cascade="all,delete")
    __table_args__ = (db.UniqueConstraint('user_id', 'datetime_id', name='name_datetime_day_uc'),)

    @staticmethod
    def generate_fake(count, username):

        pattern_not_accepted = re.compile('[&/]+')

        user = User.query.filter_by(username=username).first()
        if user is None:
            return "Please enter a correct username"
        elif user.role.name.lower() == 'student':
            return "Students cannot have ECAs"
        for i in range(count):

            eca = Eca.query.filter_by(user=user).all()
            user_eca_days = [eca_day.datetime.day for eca_day in eca] if len(eca) > 0 else []  # Gets all the
            #  days of the ECA that the user has or assign empty list if there are no ecas

            if len(user_eca_days) < 7:  # Means that there are still ECAs that can be created
                random_day = forgery_py.date.day_of_week()
                while random_day in user_eca_days:
                    random_day = forgery_py.date.day_of_week()
                    continue
                else:
                    datetime_eca = Datetime(start_time=datetime.time(random.randint(8, 23), random.randint(8, 59)),
                                            end_time=datetime.time(random.randint(8, 23), random.randint(8, 59)))
                    datetime_eca.day = random_day
                    # This is to make sure that end_time is always greater than start_time
                    while datetime_eca.end_time <= datetime_eca.start_time:
                        datetime_eca.end_time = datetime.time(random.randint(8, 23), random.randint(8, 59))

                    random_industry = forgery_py.name.industry()
                    while bool(pattern_not_accepted.findall(random_industry)) is True:
                        random_industry = forgery_py.name.industry()

                    eca = Eca(name=random_industry, max_people=random.randint(1, 13),
                              max_waiting_list=random.randint(0, 5), datetime=datetime_eca,
                              location=forgery_py.address.street_address(), user=user,
                              brief_description=forgery_py.lorem_ipsum.title(),
                              essentials=forgery_py.lorem_ipsum.sentences(quantity=3))
                    db.session.add(eca)

                    try:
                        db.session.commit()
                    except IntegrityError:
                        db.session.rollback()
            else:
                return "You reached your maximum amount of ECAs"

    def __repr__(self):
        return "<Eca {}>".format(self.name)


class Datetime(db.Model):

    __tablename__ = 'datetimes'

    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(16))
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    eca = db.relationship('Eca', back_populates='datetime')
    __table_args__ = (db.UniqueConstraint('day', 'start_time', 'end_time', name='day_start_end_time_uc'),)

    def __repr__(self):
        return "<Datetime: {} -> Start: {} End: {}>".format(self.day, self.start_time, self.end_time)


class Registration(db.Model):

    __tablename__ = 'registrations'

    id = db.Column(db.Integer, primary_key=True)
    eca_id = db.Column('eca_id', db.ForeignKey('ecas.id'), nullable=False)
    user_id = db.Column('user_id', db.ForeignKey('users.id'), nullable=False)
    in_waiting_list = db.Column(db.Boolean, default=False)
    eca = db.relationship('Eca', back_populates='registration', cascade="all,delete")
    user = db.relationship('User', back_populates='registration')
    attendance = db.relationship('Attendance', back_populates='registration')
    __table_args__ = (db.UniqueConstraint('user_id', 'eca_id', name='user_eca_uc'),)

    @staticmethod
    def join_full_fake(eca_name, in_waiting_list=False):
        eca = Eca.query.filter_by(name=eca_name).first()
        if eca is None:
            return "Please enter a correct ECA"
        else:
            user_count = User.query.count()
            max_people = eca.max_people if in_waiting_list is False else eca.max_waiting_list
            while len(Registration.query.filter_by(eca=eca, in_waiting_list=in_waiting_list).all()) != max_people:
                    user = User.query.offset(random.randint(0, user_count - 1)).first()
                    if user.role.name.lower() == 'teacher':  # Teachers cannot join into the ECA
                        continue
                    student_ecas_joined = Registration.query.filter_by(user=user).all()
                    students_ecas_days = [eca_day.eca.datetime.day for eca_day in student_ecas_joined]\
                        if len(student_ecas_joined) > 0 else []
                    if eca.datetime.day in students_ecas_days:
                        continue
                    registration_user = Registration(eca=eca, user=user, in_waiting_list=in_waiting_list)
                    db.session.add(registration_user)
                    try:
                        db.session.commit()
                    except IntegrityError:
                        db.session.rollback()

    @staticmethod
    def join_all_fake(in_waiting_list=False):
        all_ecas_names = [eca_name.name for eca_name in Eca.query.all()]
        for name in all_ecas_names:
            Registration.join_full_fake(name, in_waiting_list)

    def __repr__(self):
        return "<Registration: {} -> {}>".format(self.user.username, self.eca.name)


class Attendance(db.Model):

    __tablename__ = 'attendances'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    attended = db.Column(db.Boolean, nullable=False)
    registration_id = db.Column('registration_id', db.ForeignKey('registrations.id'), nullable=False)
    registration = db.relationship('Registration', back_populates='attendance', cascade="all,delete")
    __table_args__ = (db.UniqueConstraint('registration_id', 'date', name='registration_date_uc'),)

    @staticmethod
    def generate_fake_eca_attendance(count, eca, attended):
        eca = Eca.query.filter_by(name=eca).first()
        if eca is None:
            return "ECA does not exist"
        registrations_users_in_eca = Registration.query.filter_by(eca=eca).all()
        for registration in registrations_users_in_eca:
            for i in range(count):
                date = datetime.date(2018, random.randint(1,12), random.randint(1,28))
                db.session.add(Attendance(date=date, attended=attended, registration=registration))
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()

    @staticmethod
    def generate_fake_attendance(count, attended):
        all_ecas_names = [eca_name.name for eca_name in Eca.query.all()]
        for name in all_ecas_names:
            Attendance.generate_fake_eca_attendance(count, name, attended)

    def __repr__(self):
        return "Attendance: {} -> {} | {}".format(self.registration.user.username, self.registration.eca.name,
                                                  self.date)


@login.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


def setup_db():
    db.create_all()
    Role.insert_roles()
    User.add_main_users()
    User.generate_fake(int(input('Teacher\'s account  to create\n> ')), 'Teacher')
    User.generate_fake(int(input('Student\'s account  to create\n> ')), 'Student')
    all_teachers = User.query.filter_by(role=Role.query.filter_by(name='Teacher').first()).all()
    for teacher in all_teachers:
        Eca.generate_fake(4, teacher.username)
