import datetime

from flask import render_template, redirect, url_for
from flask_login import current_user

from app import app
from app.decorators import check_user_confirmed
from app.models import Eca, Registration, WaitingList


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
            ecas_joined = Registration.query.filter_by(user=current_user).all()
            ecas_joined += WaitingList.query.filter_by(user=current_user).all()
            return render_template('student_dashboard.html',
                                   title="Student's Dashboard", ecas_joined=ecas_joined,
                                   current_user=current_user, Registration=Registration)

    return redirect(url_for('auth.login'))
