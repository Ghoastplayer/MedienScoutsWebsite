from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from flask_talisman import Talisman
from flask import Flask
from flask_login import LoginManager, current_user
from flask_wtf import CSRFProtect
from sqlalchemy import text  # Import text function

from .models import db, User, ProblemTicket, ProblemTicketUser, TicketHistory, TrainingTicket, TrainingTicketUser, \
    MiscTicket, MiscTicketUser
import config

app = Flask(__name__)
app.config.from_object(config)

csrf = CSRFProtect(app)

csp = {
    'default-src': [
        '\'self\'',
        'https://stackpath.bootstrapcdn.com',  # Allow Bootstrap CDN
        'https://cdnjs.cloudflare.com',  # Allow other CDNs if needed
        'https://cdn.jsdelivr.net'  # Allow jsDelivr CDN
    ],
    'script-src': [
        '\'self\'',
        '\'unsafe-inline\'',  # Allow inline scripts
        'https://stackpath.bootstrapcdn.com',  # Allow Bootstrap scripts
        'https://cdnjs.cloudflare.com',  # Allow other scripts if needed
        'https://cdn.jsdelivr.net'  # Allow jsDelivr scripts
    ],
    'style-src': [
        '\'self\'',
        '\'unsafe-inline\'',  # Allow inline styles
        'https://stackpath.bootstrapcdn.com',  # Allow Bootstrap styles
        'https://cdnjs.cloudflare.com',  # Allow other styles if needed
        'https://cdn.jsdelivr.net'  # Allow jsDelivr styles
    ],
    'font-src': [
        '\'self\'',
        'https://cdnjs.cloudflare.com',  # Allow Font Awesome fonts
        'https://cdn.jsdelivr.net'  # Allow jsDelivr fonts
    ],
    'img-src': [
        '\'self\'',
        'data:'  # Allow data URLs for images
    ]
}

# Initialize Talisman with the CSP
talisman = Talisman(app, content_security_policy=csp)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Check if the database is available
def check_database():
    try:
        with app.app_context():
            db.session.execute(text('SELECT 1'))
        return True
    except Exception as e:
        print(f'Database connection error: {e}')
        return False

database_available = check_database()

# Route all access to 503 if the database is not available
@app.before_request
def before_request():
    if not database_available:
        print('Service Unavailable: Database connection error')
        return ("Service Unavailable "
                "Try again later!"), 503


def delete_old_tickets():
    threshold_date = datetime.utcnow() - timedelta(days=5*365)

    # Delete old ProblemTickets and related entries
    old_problem_tickets = ProblemTicket.query.filter(ProblemTicket.created_at < threshold_date).all()
    for ticket in old_problem_tickets:
        ProblemTicketUser.query.filter_by(problem_ticket_id=ticket.id).delete()
        TicketHistory.query.filter_by(ticket_id=ticket.id, ticket_type='problem').delete()
        db.session.delete(ticket)

    # Delete old TrainingTickets and related entries
    old_training_tickets = TrainingTicket.query.filter(TrainingTicket.created_at < threshold_date).all()
    for ticket in old_training_tickets:
        TrainingTicketUser.query.filter_by(training_ticket_id=ticket.id).delete()
        TicketHistory.query.filter_by(ticket_id=ticket.id, ticket_type='training').delete()
        db.session.delete(ticket)

    # Delete old MiscTickets and related entries
    old_misc_tickets = MiscTicket.query.filter(MiscTicket.created_at < threshold_date).all()
    for ticket in old_misc_tickets:
        MiscTicketUser.query.filter_by(misc_ticket_id=ticket.id).delete()
        TicketHistory.query.filter_by(ticket_id=ticket.id, ticket_type='misc').delete()
        db.session.delete(ticket)

    db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(func=delete_old_tickets, trigger="interval", days=1)
scheduler.start()

# Shut down the scheduler when exiting the app
import atexit
atexit.register(lambda: scheduler.shutdown())

from . import routes