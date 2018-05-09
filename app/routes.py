import calendar
import datetime

from flask import render_template, redirect, url_for
from flask_login import current_user

from app import app
from app.decorators import check_user_confirmed
from app.models import Eca, Registration, Datetime


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', e=e), 404


@app.errorhandler(403)
def page_not_found(e):
    return render_template('error.html', e=e), 403


@app.errorhandler(500)
def page_not_found(e):
    return render_template('error.html', e=e), 500


@app.route('/')
@check_user_confirmed
def index():
    if current_user.is_authenticated:
        today_weekday_num = datetime.datetime.today().weekday()
        today_weekday_name = calendar.day_name[today_weekday_num]
        if current_user.role.name.lower() == 'teacher':
            ecas_by_user = Eca.query.filter_by(user=current_user).all()
            today_eca = Eca.query.filter_by(user=current_user, is_active=True).join(Datetime).\
                filter_by(day=today_weekday_name).first()

            return render_template('teacher_dashboard.html', title="Teacher's Dashboard",
                                   num_ecas_by_user=len(ecas_by_user), ecas_by_user=ecas_by_user,
                                   next_eca=get_next_eca(ecas_by_user, today_eca))
        elif current_user.role.name.lower() == 'student':
            ecas_joined = Registration.query.filter_by(user=current_user).all()
            today_eca = Registration.query.filter_by(user=current_user).join(Eca).filter_by(is_active=True).\
                join(Datetime).filter_by(day=today_weekday_name).first()
            if today_eca is not None:
                today_eca = today_eca.eca
            return render_template('student_dashboard.html',
                                   title="Student's Dashboard", ecas_joined=ecas_joined,
                                   current_user=current_user, Registration=Registration,
                                   next_eca=get_next_eca(ecas_joined, today_eca))

    return redirect(url_for('auth.login'))


def get_next_eca(ecas, today_eca):

    # This is to ensure that None will be returned if there are no ECAs created by the teacher or if there are no
    # registrations made by the student
    if len(ecas) == 0:
        return None
    # The following code will be used to get the next ECA for the student and the teacher
    day_names = calendar.day_name[:]
    day_nums = [i for i in range(7)]
    # Create dictionary for the day names and the day numbers
    day_num_names = dict(zip(day_names, day_nums))
    if isinstance(ecas[0], Eca):
        eca_days = [eca_day.datetime.day.title() for eca_day in ecas]
    else:
        eca_days = [registration_eca_day.eca.datetime.day.title() for registration_eca_day in ecas]
    eca_days_nums = [day_num_names[i] for i in eca_days]
    eca_days_nums.sort()
    # Checks if there is an ECA today and if the time right now is less than the start time of the eca
    # If all the conditions above are true, then the next eca will be today's ECA
    if today_eca is not None and datetime.datetime.today().time() < today_eca.datetime.start_time:
        return today_eca
    else:
        next_eca_day_name = day_names[get_next_number(eca_days_nums, datetime.datetime.today().weekday())]

        if isinstance(ecas[0], Eca):
            next_eca = Eca.query.filter_by(user=current_user, is_active=True).join(Datetime).\
                filter_by(day=next_eca_day_name).first()
        else:
            next_eca = Registration.query.filter_by(user=current_user).join(Eca).filter_by(is_active=True).\
                join(Datetime).filter_by(day=next_eca_day_name).first()
        try:
            return next_eca.eca
        except AttributeError:
            return next_eca


def get_next_number(arr, target):
    """
    Function to get the next number of the list, for example if we have a list that contains the following data:
    [1,3,5]
    And the target parameter is 2, then the function will return 3. Also, if we have a list that contains the following
    data: [1,3] and the target parameter is 4 then the function will return the first item of the list

    :param arr:
    :param target:
    :return:
    """
    count = 0
    while True:
        # If the last item from the list is bigger than the number then it means that there are more items on the right
        # therefore count is increased
        if arr[-1] > target:
            try:
                count += 1
                return arr[arr.index(target + count)]
            except ValueError:
                continue
        # If the last item from the list is smaller or equal
        # than the number then it means that the next eca would be in the
        # first item of the list
        elif arr[-1] <= target:
            return arr[0]
