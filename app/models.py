import datetime
import random

import forgery_py
from flask_login import UserMixin, current_user
from jwt import encode, decode, DecodeError, ExpiredSignatureError
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login, app


class User(UserMixin, db.Model):

    count_password_request = 0
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(128), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role_id = db.Column('role_id', db.ForeignKey('role.id'), nullable=False)
    role = db.relationship('Role', back_populates='user')
    confirmed = db.Column(db.Boolean, default=False, nullable=False)
    eca = db.relationship('Eca', back_populates='user')
    registration = db.relationship('Registration', back_populates='user')
    waiting_list = db.relationship('WaitingList', back_populates='user')

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
        return encode({'confirm': self.id, 'current_email': current_email, 'new_email':new_email,
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
            return False
        if decoded.get('confirm') != self.id:
            return False
        elif decoded.get('current_email') != current_user.email:
            return False
        else:
            return True

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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    max_people = db.Column(db.Integer)
    max_waiting_list = db.Column(db.Integer)
    datetime_id = db.Column('datetime_id', db.ForeignKey('datetime.id'), nullable=False)
    datetime = db.relationship('Datetime', back_populates='eca')
    location = db.Column(db.String(64), nullable=False)
    user_id = db.Column('user_id', db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='eca')
    registration = db.relationship('Registration', back_populates='eca')
    brief_description = db.Column(db.String(128))
    essentials = db.Column(db.Text)
    waiting_list = db.relationship('WaitingList', back_populates='eca')
    is_active = db.Column(db.Boolean, default=True)

    @staticmethod
    def generate_fake(count, username):
        user = User.query.filter_by(username=username).first()
        if user is None:
            return "Please enter a correct username"
        elif user.role.name.lower() == 'student':
            return "Students cannot have ECAs"
        else:
            for i in range(count):
                datetime_eca = Datetime(day=forgery_py.date.day_of_week(),
                                        start_time=datetime.time(random.randint(8, 23), random.randint(8, 59)),
                                        end_time=datetime.time(random.randint(8, 23), random.randint(8, 59)))

                # This is to make sure that end_time is always greater than start_time
                while datetime_eca.end_time <= datetime_eca.start_time:
                    datetime_eca.end_time = datetime.time(random.randint(8, 23), random.randint(8, 59))

                eca = Eca(name=forgery_py.name.industry(), max_people=random.randint(1, 30),
                          max_waiting_list=random.randint(0, 20), datetime=datetime_eca,
                          location=forgery_py.address.street_address(), user=user,
                          brief_description=forgery_py.lorem_ipsum.title(),
                          essentials=forgery_py.lorem_ipsum.sentences(quantity=3))
                db.session.add(eca)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()

    def __repr__(self):
        return "<Eca {}>".format(self.name)


class Datetime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(16))
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    eca = db.relationship('Eca', back_populates='datetime')

    def __repr__(self):
        return "<Datetime: {} -> Start: {} End: {}>".format(self.day, self.start_time, self.end_time)


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eca_id = db.Column('eca_id', db.ForeignKey('eca.id'), nullable=False)
    eca = db.relationship('Eca', back_populates='registration')
    user_id = db.Column('user_id', db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='registration')
    attendance = db.relationship('Attendance', back_populates='registration')
    __table_args__ = (db.UniqueConstraint('user_id', 'eca_id', name='user_eca_uc'),)

    @staticmethod
    def join_full_fake(eca_name):
        eca = Eca.query.filter_by(name=eca_name).first()
        if eca is None:
            return "Please enter a correct ECA"
        else:
            user_count = User.query.count()

            while len(eca.registration) != eca.max_people:
                    user = User.query.offset(random.randint(0, user_count - 1)).first()
                    registration_user = Registration(eca=eca, user=user)
                    db.session.add(registration_user)
                    try:
                        db.session.commit()
                    except IntegrityError:
                        db.session.rollback()

    @staticmethod
    def join_all_fake():
        all_ecas_names = [eca_name.name for eca_name in Eca.query.all()]
        for name in all_ecas_names:
            Registration.join_full_fake(name)

    def __repr__(self):
        return "<Registration: {} -> {}>".format(self.user.username, self.eca.name)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column('registration_id', db.ForeignKey('registration.id'), nullable=False)
    registration = db.relationship('Registration', back_populates='attendance')
    date = db.Column(db.Date, nullable=False)
    attended = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return "Attendance: {} -> {} | {}".format(self.registration.user.username, self.registration.eca.name,
                                                  self.date)


class WaitingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='waiting_list')
    eca_id = db.Column('eca_id', db.ForeignKey('eca.id'), nullable=False)
    eca = db.relationship('Eca', back_populates='waiting_list')
    __table_args__ = (db.UniqueConstraint('user_id', 'eca_id', name='user_eca_uc'),)

    @staticmethod
    def add_waiting_list(eca_name, count):
        user_count = User.query.count()
        for _ in range(count):
            user = User.query.offset(random.randint(0, user_count - 1)).first()
            eca = Eca.query.filter_by(name=eca_name).first()
            db.session.add(WaitingList(user=user, eca=eca))
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


@login.user_loader
def user_loader(user_id):
    return User.query.get(user_id)
