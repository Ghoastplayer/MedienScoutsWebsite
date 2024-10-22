import os
from datetime import datetime, timedelta

from flask import jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from app import app
from app.decorators import admin_required
from app.forms import MessageForm, LoginForm
from app.models import Message, MiscTicket, TrainingTicket, ProblemTicket, ProblemTicketUser, \
    TrainingTicketUser, MiscTicketUser, TicketHistory
from email_tools import send_ticket_link, notify_admin


@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def home():
    member_count = User.query.filter_by(active=True).count()
    return render_template('home.html', member_count=member_count)


@app.route('/members')
def members():
    active_members = User.query.filter_by(active=True).all()  # Aktive Mitglieder abrufen
    inactive_members = User.query.filter_by(active=False).all()  # Inaktive Mitglieder abrufen
    return render_template('members.html', active_members=active_members, inactive_members=inactive_members)


@app.route('/ticketverwaltung')
@login_required
def ticket_verwaltung():
    # Fetch all open tickets
    open_problem_tickets = ProblemTicket.query.filter_by(status_id=1).all()
    open_training_tickets = TrainingTicket.query.filter_by(status_id=1).all()
    open_misc_tickets = MiscTicket.query.filter_by(status_id=1).all()

    # Add type attribute to each ticket
    for ticket in open_problem_tickets:
        ticket.type = 'problem'
    for ticket in open_training_tickets:
        ticket.type = 'training'
    for ticket in open_misc_tickets:
        ticket.type = 'misc'

    # Fetch all tickets claimed by the current user that are not closed (status_id != 4)
    my_problem_tickets = ProblemTicket.query.join(ProblemTicketUser).filter(
        ProblemTicketUser.user_id == current_user.id,
        ProblemTicket.status_id != 4
    ).all()
    my_training_tickets = TrainingTicket.query.join(TrainingTicketUser).filter(
        TrainingTicketUser.user_id == current_user.id,
        TrainingTicket.status_id != 4
    ).all()
    my_misc_tickets = MiscTicket.query.join(MiscTicketUser).filter(
        MiscTicketUser.user_id == current_user.id,
        MiscTicket.status_id != 4
    ).all()

    # Add type attribute to each claimed ticket
    for ticket in my_problem_tickets:
        ticket.type = 'problem'
    for ticket in my_training_tickets:
        ticket.type = 'training'
    for ticket in my_misc_tickets:
        ticket.type = 'misc'

    # Combine all claimed tickets
    my_tickets = my_problem_tickets + my_training_tickets + my_misc_tickets

    # Count total open tickets
    total_open_tickets = len(open_problem_tickets) + len(open_training_tickets) + len(open_misc_tickets)

    return render_template('ticketverwaltung.html',
                           open_problem_tickets=open_problem_tickets,
                           open_training_tickets=open_training_tickets,
                           open_misc_tickets=open_misc_tickets,
                           my_tickets=my_tickets,
                           total_open_tickets=total_open_tickets)


@app.route('/ticket/<string:ticket_type>/<int:ticket_id>/details')
@login_required
def ticket_details(ticket_type, ticket_id):
    if ticket_type == 'problem':
        ticket = ProblemTicket.query.get(ticket_id)
    elif ticket_type == 'training':
        ticket = TrainingTicket.query.get(ticket_id)
    elif ticket_type == 'misc':
        ticket = MiscTicket.query.get(ticket_id)
    else:
        flash('Invalid ticket type.', 'danger')
        return redirect(url_for('ticket_verwaltung'))

    ticket_history = TicketHistory.query.filter_by(ticket_type=ticket_type, ticket_id=ticket_id).order_by(
        TicketHistory.created_at).all()

    return render_template('ticket_details.html', ticket=ticket, ticket_type=ticket_type, ticket_history=ticket_history)


@app.route('/ticket/<int:ticket_id>/claim', methods=['POST'])
@login_required
def claim_ticket(ticket_id):
    user_id = request.form.get('user_id')

    ticket_type = request.form.get('ticket_type')

    if ticket_type == 'problem':
        ticket = ProblemTicket.query.get(ticket_id)
        ticket_user = ProblemTicketUser(ticket_user_id=None, problem_ticket_id=ticket_id, user_id=user_id)
    elif ticket_type == 'training':
        ticket = TrainingTicket.query.get(ticket_id)
        ticket_user = TrainingTicketUser(ticket_user_id=None, training_ticket_id=ticket_id, user_id=user_id)
    elif ticket_type == 'misc':
        ticket = MiscTicket.query.get(ticket_id)
        ticket_user = MiscTicketUser(ticket_user_id=None, misc_ticket_id=ticket_id, user_id=user_id)

    ticket.status_id = 2

    db.session.add(ticket_user)
    db.session.commit()

    return redirect(url_for('ticket_details', ticket_id=ticket_id, ticket_type=ticket_type))


@app.route('/ticket/<int:ticket_id>/request_help', methods=['POST'])
@login_required
def request_help(ticket_id):
    ticket_type = request.form.get('ticket_type')
    print(f'Ticket Type: {ticket_type}')
    if ticket_type == 'problem':
        ticket = ProblemTicket.query.get(ticket_id)
    elif ticket_type == 'training':
        ticket = TrainingTicket.query.get(ticket_id)
    elif ticket_type == 'misc':
        ticket = MiscTicket.query.get(ticket_id)
    else:
        flash('Invalid ticket type.', 'danger')
        return redirect(url_for('ticket_details', ticket_id=ticket_id, ticket_type=ticket_type))

    notify_admin(ticket, ticket_type, 'Help is requested for the following ticket:')
    flash('Help request has been sent for ticket ID: {}'.format(ticket_id), 'info')
    return redirect(url_for('ticket_details', ticket_id=ticket_id, ticket_type=ticket_type))


#TODO: Ticket Client benachrichtigen
@app.route('/ticket/<int:ticket_id>/submit_response', methods=['POST'])
@login_required
def submit_response(ticket_id):
    response_message = request.form.get('response_message')
    ticket_type = request.form.get('ticket_type')
    if not ticket_type:
        flash('Ticket type is required.', 'danger')
        return redirect(url_for('ticket_details', ticket_id=ticket_id, ticket_type=ticket_type))

    # Log the ticket message
    log_ticket_message(ticket_type, ticket_id, response_message, 'user')

    # Update the ticket status to 3
    if ticket_type == 'problem':
        ticket = ProblemTicket.query.get(ticket_id)
    elif ticket_type == 'training':
        ticket = TrainingTicket.query.get(ticket_id)
    elif ticket_type == 'misc':
        ticket = MiscTicket.query.get(ticket_id)

    ticket.status_id = 3
    db.session.commit()

    flash('Response has been submitted for ticket ID: {}'.format(ticket_id), 'info')
    return redirect(url_for('ticket_details', ticket_id=ticket_id, ticket_type=ticket_type))


@app.route('/ticket/<int:ticket_id>/mark_solved', methods=['POST'])
@login_required
def mark_ticket_solved(ticket_id):
    print(f'Ticket ID: {ticket_id}')
    print("Trying to find ticket_type")
    ticket_type = request.form.get('ticket_type')
    print(f'Ticket Type: {ticket_type}')

    if ticket_type == 'problem':
        ticket = ProblemTicket.query.get(ticket_id)
    elif ticket_type == 'training':
        ticket = TrainingTicket.query.get(ticket_id)
    elif ticket_type == 'misc':
        ticket = MiscTicket.query.get(ticket_id)
    else:
        flash('Invalid ticket type.', 'danger')
        return redirect(url_for('ticket_details', ticket_id=ticket_id, ticket_type=ticket_type))

    if ticket:
        ticket.status_id = 4
        db.session.commit()
        flash('Ticket marked as solved.', 'success')
    else:
        flash('Ticket not found.', 'danger')

    return redirect(url_for('ticket_details', ticket_id=ticket_id, ticket_type=ticket_type))

@app.route('/ticket/<int:ticket_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_ticket(ticket_id):
    ticket_type = request.form.get('ticket_type')
    if ticket_type == 'problem':
        ticket = ProblemTicket.query.get(ticket_id)
        ProblemTicketUser.query.filter_by(problem_ticket_id=ticket_id).delete()
    elif ticket_type == 'training':
        ticket = TrainingTicket.query.get(ticket_id)
        TrainingTicketUser.query.filter_by(training_ticket_id=ticket_id).delete()
    elif ticket_type == 'misc':
        ticket = MiscTicket.query.get(ticket_id)
        MiscTicketUser.query.filter_by(misc_ticket_id=ticket_id).delete()
    else:
        flash('Invalid ticket type.', 'danger')
        return redirect(url_for('ticket_verwaltung'))

    db.session.delete(ticket)
    TicketHistory.query.filter_by(ticket_id=ticket_id, ticket_type=ticket_type).delete()

    if ticket:
        db.session.delete(ticket)
        db.session.commit()
        flash('Ticket deleted successfully.', 'success')
    else:
        flash('Ticket not found.', 'danger')

    return redirect(url_for('ticket_verwaltung'))


@app.route('/send_ticket', methods=['GET', 'POST'])
def send_ticket():
    if request.method == 'POST':
        ticket_type = request.form.get('ticket_type')
        print(f'Ticket type: {ticket_type}')

        if ticket_type == 'problem':
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email_problem')
            print(f'First Name: {first_name}, Last Name: {last_name}, Email: {email}')
            class_stufe = request.form.get('class')
            serial_number = request.form.get('serial_number')
            problem_description = request.form.get('problem_description')
            steps = request.form.getlist('steps')
            steps_taken = ", ".join(steps)
            photo = request.files.get('photo')
            print(
                f'Class: {class_stufe}, Serial Number: {serial_number}, Problem Description: {problem_description}, Steps Taken: {steps_taken}, Photo: {photo}')

            # TODO: Implement file upload
            photo_path = None
            if photo:
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_path = filename
                print(f'Photo Path: {photo_path}')

            ticket = ProblemTicket(
                first_name=first_name,
                last_name=last_name,
                email=email,
                class_name=class_stufe,
                serial_number=serial_number,
                problem_description=problem_description,
                steps_taken=steps_taken,
                photo=photo_path,
                status_id=1
            )

            db.session.add(ticket)

        elif ticket_type == 'fortbildung':
            class_teacher = request.form.get('class_teacher')
            email = request.form.get('email_fortbildung')
            training_type = request.form.get('training_type')
            training_reason = request.form.get('training_reason')
            proposed_date = request.form.get('proposed_date')
            print(
                f'Class Teacher: {class_teacher}, Training Type: {training_type}, Training Reason: {training_reason}, Proposed Date: {proposed_date}')

            ticket = TrainingTicket(
                class_teacher=class_teacher,
                email=email,
                training_type=training_type,
                training_reason=training_reason,
                proposed_date=proposed_date,
                status_id=1
            )

            db.session.add(ticket)

        else:
            first_name = request.form.get('first_name_sonstiges')
            last_name = request.form.get('last_name_sonstiges')
            message = request.form.get('message_sonstiges')
            email = request.form.get('email_sonstiges')
            print(f'Message: {message}')

            ticket = MiscTicket(
                first_name=first_name,
                last_name=last_name,
                email=email,
                message=message,
                status_id=1
            )

            db.session.add(ticket)

        db.session.commit()

        # Generate token and send email with the link
        send_ticket_link(ticket)

        flash(f'Ticket submitted successfully! Type: {ticket_type}', 'success')
        return redirect(url_for('home'))

    return render_template('ticket.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if not user.active:
                flash('Your account is inactive. Please contact the administrator.', 'danger')
                return redirect(url_for('login'))
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('home'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)


@login_required
@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route('/forum', methods=['GET', 'POST'])
@login_required
def forum():
    form = MessageForm()
    if form.validate_on_submit():
        role = 'Admin' if current_user.is_admin() else 'Member'
        message = Message(author=current_user.username, role=role, content=form.content.data)
        db.session.add(message)
        db.session.commit()
        flash('Your message has been posted.', 'success')
        return redirect(url_for('forum'))

    page = request.args.get('page', 1, type=int)
    messages = Message.query.order_by(Message.timestamp.desc()).paginate(page=page, per_page=5)
    return render_template('forum.html', form=form, messages=messages.items, pagination=messages)

@app.route('/load_more_messages/<int:page>', methods=['GET'])
@login_required
def load_more_messages(page):
    messages = Message.query.order_by(Message.timestamp.desc()).paginate(page=page, per_page=5)
    return jsonify({
        'messages': [{
            'id': message.id,
            'author': message.author,
            'role': message.role,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'deleted': message.deleted
        } for message in messages.items],
        'more_messages': messages.has_next,
        'is_admin': current_user.is_admin()
    })


@app.route('/delete_message/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def delete_message(message_id):
    message = Message.query.get(message_id)
    if message:
        message.content = f'This Post was deleted by the Admin on {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}'
        message.deleted = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Message not found'}), 404


@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')


@app.route('/archiv')
@login_required
def archiv():
    solved_problem_tickets = ProblemTicket.query.filter_by(status_id=4).all()
    solved_training_tickets = TrainingTicket.query.filter_by(status_id=4).all()
    solved_misc_tickets = MiscTicket.query.filter_by(status_id=4).all()

    return render_template('archiv.html',
                           solved_problem_tickets=solved_problem_tickets,
                           solved_training_tickets=solved_training_tickets,
                           solved_misc_tickets=solved_misc_tickets)

@app.route('/admin/panel')
@login_required
@admin_required
def admin_panel():
    # Calculate statistics
    six_months_ago = datetime.utcnow() - timedelta(days=6*30)
    total_tickets = (
        db.session.query(ProblemTicket).filter(ProblemTicket.created_at >= six_months_ago).count() +
        db.session.query(TrainingTicket).filter(TrainingTicket.created_at >= six_months_ago).count() +
        db.session.query(MiscTicket).filter(MiscTicket.created_at >= six_months_ago).count()
    )
    solved_tickets = (
        db.session.query(ProblemTicket).filter(ProblemTicket.created_at >= six_months_ago, ProblemTicket.status_id == 4).count() +
        db.session.query(TrainingTicket).filter(TrainingTicket.created_at >= six_months_ago, TrainingTicket.status_id == 4).count() +
        db.session.query(MiscTicket).filter(MiscTicket.created_at >= six_months_ago, MiscTicket.status_id == 4).count()
    )

    # User statistics
    user_stats = db.session.query(
        User.first_name,
        User.last_name,
        db.func.count(ProblemTicket.id).label('problem_count'),
        db.func.count(TrainingTicket.id).label('training_count'),
        db.func.count(MiscTicket.id).label('misc_count')
    ).outerjoin(ProblemTicketUser, ProblemTicketUser.user_id == User.id).outerjoin(
        ProblemTicket, ProblemTicket.id == ProblemTicketUser.problem_ticket_id).outerjoin(
        TrainingTicketUser, TrainingTicketUser.user_id == User.id).outerjoin(
        TrainingTicket, TrainingTicket.id == TrainingTicketUser.training_ticket_id).outerjoin(
        MiscTicketUser, MiscTicketUser.user_id == User.id).outerjoin(
        MiscTicket, MiscTicket.id == MiscTicketUser.misc_ticket_id).group_by(
        User.first_name, User.last_name).all()

    return render_template('admin_panel.html',
                           total_tickets=total_tickets,
                           solved_tickets=solved_tickets,
                           user_stats=user_stats)

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import User, db, RoleEnum, RankEnum

@app.route('/members/administration', methods=['GET', 'POST'])
@login_required
@admin_required
def members_administration():
    if request.method == 'POST':
        if 'create_user' in request.form:
            new_user = User(
                username=request.form.get('new_username'),
                first_name=request.form.get('new_first_name'),
                last_name=request.form.get('new_last_name'),
                email=request.form.get('new_email'),
                role=request.form.get('new_role'),
                rank=request.form.get('new_rank'),
                active=True,
                active_from=datetime.utcnow()
            )
            new_user.set_password(request.form.get('new_password'))
            db.session.add(new_user)
            db.session.commit()
            flash('New user created successfully.', 'success')
        else:
            user_id = request.form.get('user_id')
            user = User.query.get(user_id)
            if user:
                user.username = request.form.get('username')
                user.first_name = request.form.get('first_name')
                user.last_name = request.form.get('last_name')
                user.email = request.form.get('email')
                user.role = request.form.get('role')
                user.rank = request.form.get('rank')
                if 'set_inactive' in request.form:
                    user.active = False
                    user.active_until = datetime.utcnow()
                elif 'set_active' in request.form:
                    user.active = True
                    user.active_until = None
                new_password = request.form.get('new_password')
                if new_password:
                    user.set_password(new_password)
                db.session.commit()
                flash('User updated successfully.', 'success')
            else:
                flash('User not found.', 'danger')
        return redirect(url_for('members_administration'))

    active_users = User.query.filter_by(active=True).all()
    inactive_users = User.query.filter_by(active=False).all()
    return render_template('members_administration.html', active_users=active_users, inactive_users=inactive_users, roles=RoleEnum, ranks=RankEnum)

@app.route('/impressum')
def impressum():
    return render_template('impressum.html')


#TODO: User benachrichtigen bei neuer Nachricht
@app.route('/ticket/<token>', methods=['GET', 'POST'])
def view_ticket(token):
    ticket_type = None
    for TicketModel, type_name in [(ProblemTicket, 'problem'), (TrainingTicket, 'training'), (MiscTicket, 'misc')]:
        ticket = TicketModel.verify_token(token)
        if ticket:
            ticket_type = type_name
            break

    if not ticket:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        response_message = request.form.get('response_message')
        log_ticket_message(ticket_type, ticket.id, response_message, 'non-member')
        flash('Your response has been submitted.', 'success')
        return redirect(url_for('view_ticket', token=token))

    ticket_history = TicketHistory.query.filter_by(ticket_type=ticket_type, ticket_id=ticket.id).order_by(TicketHistory.created_at).all()

    return render_template('view_ticket.html', ticket=ticket, token=token, ticket_history=ticket_history)
def log_ticket_message(ticket_type, ticket_id, message, author_type):
    history_entry = TicketHistory(
        ticket_type=ticket_type,
        ticket_id=ticket_id,
        message=message,
        author_type=author_type
    )
    db.session.add(history_entry)
    db.session.commit()
