import enum

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import DateTime

db = SQLAlchemy()

class RankEnum(enum.Enum):
    KEIN = 'KEIN'
    BRONZE = 'BRONZE'
    SILBER = 'SILBER'
    GOLD = 'GOLD'
    PLATIN = 'PLATIN'



class RoleEnum(enum.Enum):
    ADMIN = 'ADMIN'
    TEACHER = 'TEACHER'
    MEMBER = 'MEMBER'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.MEMBER)
    rank = db.Column(db.Enum(RankEnum), nullable=True, default=RankEnum.KEIN)
    active = db.Column(db.Boolean, default=True)
    active_from = db.Column(DateTime, nullable=True)  # Zeitpunkt, ab dem das Mitglied aktiv ist
    active_until = db.Column(DateTime, nullable=True)  # Zeitpunkt, bis zu dem das Mitglied aktiv ist

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == RoleEnum.ADMIN

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(64), nullable=False)  # Add this line
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)  # Add this line



class TicketStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), nullable=False)

class ProblemTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(50), nullable=True)
    problem_description = db.Column(db.Text, nullable=False)
    steps_taken = db.Column(db.Text, nullable=True)
    photo = db.Column(db.String(200), nullable=True)  # Assuming file path stored
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status_id = db.Column(db.Integer, db.ForeignKey('ticket_status.id'), default=1)  # Default to "open"

class TrainingTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_teacher = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    training_type = db.Column(db.String(100), nullable=False)
    training_reason = db.Column(db.Text, nullable=True)
    proposed_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status_id = db.Column(db.Integer, db.ForeignKey('ticket_status.id'), default=1)

class MiscTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status_id = db.Column(db.Integer, db.ForeignKey('ticket_status.id'), default=1)

class ProblemTicketUser(db.Model):
    ticket_user_id = db.Column(db.Integer, primary_key=True)
    problem_ticket_id = db.Column(db.Integer, db.ForeignKey('problem_ticket.id'), nullable=False)  # ForeignKey to ProblemTicket
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ForeignKey to User
    assigned_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)  # Assignment timestamp

    # Relationships
    user = db.relationship('User', backref='problem_ticket_assignments')
    problem_ticket = db.relationship('ProblemTicket', backref='assigned_users')

class TrainingTicketUser(db.Model):
    ticket_user_id = db.Column(db.Integer, primary_key=True)
    training_ticket_id = db.Column(db.Integer, db.ForeignKey('training_ticket.id'), nullable=False)  # ForeignKey to TrainingTicket
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ForeignKey to User
    assigned_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)  # Assignment timestamp

    # Relationships
    user = db.relationship('User', backref='training_ticket_assignments')
    training_ticket = db.relationship('TrainingTicket', backref='assigned_users')


class MiscTicketUser(db.Model):
    ticket_user_id = db.Column(db.Integer, primary_key=True)
    misc_ticket_id = db.Column(db.Integer, db.ForeignKey('misc_ticket.id'), nullable=False)  # ForeignKey to MiscTicket
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ForeignKey to User
    assigned_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)  # Assignment timestamp

    # Relationships
    user = db.relationship('User', backref='misc_ticket_assignments')
    misc_ticket = db.relationship('MiscTicket', backref='assigned_users')

class TicketHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_type = db.Column(db.String(50), nullable=False)
    ticket_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_type = db.Column(db.String(50), nullable=False)  # New column to indicate author type

    def __init__(self, ticket_type, ticket_id, message, author_type):
        self.ticket_type = ticket_type
        self.ticket_id = ticket_id
        self.message = message
        self.author_type = author_type