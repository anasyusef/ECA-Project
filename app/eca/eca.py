from app.eca import bp
from flask import redirect, url_for, render_template
from app.forms import *
from app.models import *
from flask_login import current_user, login_required
from app.decorators import permission_required
from app.emails import send_email


@bp.route('/add_eca', methods=['GET', 'POST'])
@login_required
@permission_required('Teacher')
def add_eca():
    form = AddEca()
    if form.validate_on_submit():
        if form.day_eca.data in [i.datetime.day for i in Eca.query.filter_by(user=current_user).all()]:
            flash('You cannot have two ECAs in the same day', 'danger')
            return redirect(url_for('eca.add_eca'))
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


@bp.route('/update/<eca_name>', methods=['GET', 'POST'])
@login_required
@permission_required('Teacher')
def eca_name_edit(eca_name):
    eca_names = [eca_name.name.lower() for eca_name in Eca.query.filter_by().all()]
    if eca_name.lower() not in eca_names:
        return "ECA Not Found", 404
    form = EditEca()
    eca = Eca.query.filter_by(name=eca_name).first()
    if eca.user != current_user:
        flash('You are not allowed to edit this ECA', 'danger')
        return redirect('eca.edit_eca')
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
                flash('You cannot have two ECAs in the same day', 'danger')
                return redirect(url_for('eca.eca_name_edit', eca_name=eca_name))
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
        return redirect(url_for('eca.manage_ecas'))
    return render_template('edit_eca.html', eca_name=eca_name, form=form, eca=eca, start_time_eca=start_time_eca,
                           end_time_eca=end_time_eca)


@bp.route('/delete/<eca_name>')
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
        send_email(subject='{} ECA has been removed'.format(eca_name.title()),
                   recipients=[user.email for user in users_related_to_ecas],
                   html_body='email_eca_removed', users=users_related_to_ecas, eca_name=eca_name.title())
        Registration.query.filter_by(eca=eca_to_delete.first()).delete()
    eca_to_delete.delete()
    db.session.commit()
    flash('ECA has been deleted successfully', 'success')
    return redirect(url_for('edit_eca'))


@bp.route('/notification_eca', methods=['GET', 'POST'])
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
    if form.validate_on_submit():
        eca = Eca.query.filter_by(name=form.eca_name.data).first()
        action = form.status_notification.data if form.status_notification.data != 'custom' \
            else form.custom_status_notification.data
        email_subject = '{} - {}'.format(form.eca_name.data.title(), action.title())
        users_related_to_eca = [user.user for user in eca.registration]
        recipients = [user.email for user in users_related_to_eca]

        send_email(subject=email_subject, recipients=recipients, html_body='email_notification_eca',
                   users=users_related_to_eca, eca_name=eca.name.title(), reason=form.reason.data,
                   action=action.title())

        flash('Your notification has been sent successfully!', 'success')

    return render_template('eca_notification.html', form=form, reason_variables=reason_variables)


@bp.route('/manage_ecas')
@login_required
def manage_ecas():

    if current_user.role.name.lower() == 'teacher':
        ecas = Eca.query.filter_by(user=current_user).all()
    else:
        ecas = [student_eca.eca for student_eca in Registration.query.filter_by(user=current_user).all()]
        # Takes all the ecas that the current user is registered to

    return render_template('base_ecas_overview.html', ecas=ecas, current_user=current_user)


@app.route('/eca/delete_student/<eca_name>/')
@login_required
@permission_required('Teacher')
def delete_student(eca_name):
        user_to_delete = User.query.filter_by(id=request.args.get('id')).first()
        eca_user_related = Eca.query.filter_by(name=eca_name).first()

        if eca_user_related.user != current_user:  # This is to only allow the teacher that created the ECA to remvove
            # students from his ECA, if other teacher somehow access this link it will not be allowed to remove any
            # students from the other teacher's ECA
            return "You are not allowed to do this action", 403

        if request.args.get('action') is not None:
            if request.args.get('action') == 'remove':
                user_registration = Registration.query.filter_by(user=user_to_delete, eca=eca_user_related)
                send_email(subject='Removed from {} ECA'.format(eca_name), html_body='email_removed_from_eca',
                           recipients=[user_to_delete.email], user=user_to_delete, eca_name=eca_name)
                user_registration.delete()
                # Code to remove student from waiting list and add it to the registration list
                front_user_waiting_list = WaitingList.query.filter_by(eca=eca_user_related)
                if front_user_waiting_list.first() is not None:
                    new_user_registration = Registration(eca=eca_user_related,
                                                         user=front_user_waiting_list.first().user)

                    send_email(subject='Removed from waiting list - {} ECA'.format(eca_user_related.name),
                               html_body='email_removed_from_waiting_list',
                               recipients=[front_user_waiting_list.first().user.email],
                               user=front_user_waiting_list.first().user, eca_name=eca_name)

                    WaitingList.query.filter_by(eca=eca_user_related,
                                                user=front_user_waiting_list.first().user).delete()
                    db.session.add(new_user_registration)
            elif request.args.get('action') == 'remove_wl':
                user_waiting_list = WaitingList.query.filter_by(user=user_to_delete, eca=eca_user_related)
                user_waiting_list.delete()

        db.session.commit()
        # TODO Send email when a student is removed from the waiting list and is not added to the active list
        # TODO Remove the tick button from the waiting list
        # TODO Fix the error when removing students from the waiting list, because when a student is removed from the active list, the student from the waiting list is still added
        return 'Student Removed'


@bp.route('/join_eca', methods=['GET', 'POST'])
@login_required
@permission_required('Student')
def join_eca():
    form = JoinEca()
    ecas = Eca.query.all()
    form.eca_name.choices = [(eca.name.lower(), eca.name) for eca in ecas]
    form.eca_name.choices.insert(0, ('choose', 'Choose...'))
    if form.validate_on_submit():
        eca = Eca.query.filter_by(name=form.eca_name.data).first()

        if len(eca.registration) == eca.max_people:
            db.session.add(WaitingList(user=current_user, eca=eca))
            try:
                db.session.commit()
                flash('This ECA has reached its maximum capacity of students, you will be put on the waiting list',
                      'danger')
            except IntegrityError:
                flash('You have been already added into the waiting list of this ECA', 'danger')
                db.session.rollback()
                return redirect(url_for('eca.join_eca'))
        else:
            registration = Registration(user=current_user, eca=eca)
            db.session.add(registration)
            db.session.commit()
            flash('You have joined into {} successfully!'.format(eca.name), 'success')

    return render_template('join_eca.html', title='Join ECA', form=form, ecas=ecas)


@bp.route('/quit/<eca_name>/')
@login_required
@permission_required('Student')
def quit_eca(eca_name):
    eca = Eca.query.filter_by(name=eca_name).first()
    Registration.query.filter_by(user=current_user, eca=eca).delete()
    db.session.commit()
    flash('You have quit the {} ECA successfully!'.format(eca.name), 'success')
    return redirect(url_for('eca.manage_ecas'))