import configparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import url_for


class EmailTemplate:
    def __init__(self, subject, template_content):
        self.subject = subject
        self.template_content = template_content

    def render(self, **kwargs):
        # Fügt die Variablen in den Template-Content ein
        return self.template_content.format(**kwargs)


# Funktion zum Senden einer E-Mail mit dynamischem Template
def send_email(template, recipient, **variables):
    # Konfigurationsdatei lesen
    config = configparser.ConfigParser()
    config.read('config.ini')

    # SMTP-Konfigurationsdaten auslesen
    smtp_server = config['SMTP']['server']
    smtp_port = config['SMTP'].getint('port')
    smtp_user = config['SMTP']['user']
    smtp_password = config['SMTP']['password']

    from_email = smtp_user
    subject = template.subject
    html_content = template.render(**variables)

    # E-Mail-Nachricht erstellen
    message = MIMEMultipart('alternative')
    message['From'] = from_email
    message['To'] = recipient
    message['Subject'] = subject

    # HTML-Nachricht hinzufügen
    html_part = MIMEText(html_content, 'html')
    message.attach(html_part)

    # E-Mail senden
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, recipient, message.as_string())
        server.quit()
        print("E-Mail wurde erfolgreich gesendet.")
    except Exception as e:
        print(f"Fehler beim Senden der E-Mail: {e}")


# Beispiel-Templates
welcome_template = EmailTemplate(
    subject="Willkommen bei MedienScouts!",
    template_content="""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; color: #333; padding: 20px; }}
            .email-header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
            .email-content {{ padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); }}
            .btn {{ display: inline-block; padding: 10px 20px; background-color: #007BFF; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
            .email-footer {{ font-size: 12px; color: #777; text-align: center; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="email-header">
            <h1>Willkommen, {name}!</h1>
        </div>
        <div class="email-content">
            <p>Hallo {name},</p>
            <p>Wir freuen uns, dass wir weitere Unterstützung erhalten haben. Wenn du möchtest, kannst du direkt mit dem Bearbeiten von Tickets anfangen.</p>
            <p>Oder, wenn du möchtest, mach dich zunächst mit unserem Tool vertraut.</p>
            <p>Falls du Fragen hast, stelle sie einfach im Forum: <a href="{forum_link}" class="btn">Zum Forum</a></p>
        </div>
        <div class="email-footer">
            <p>&copy; 2024 MedienScouts | Alle Rechte vorbehalten.</p>
        </div>
    </body>
    </html>
    """
)

ticket_link_template = EmailTemplate(
    subject="Your Ticket Link",
    template_content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; color: #333; padding: 20px; }}
            .email-header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
            .email-content {{ padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); }}
            .btn {{ display: inline-block; padding: 10px 20px; background-color: #007BFF; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
            .email-footer {{ font-size: 12px; color: #777; text-align: center; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="email-header">
            <h1>Your Ticket Link</h1>
        </div>
        <div class="email-content">
            <p>Hello,</p>
            <p>You can view and reply to your ticket using the following link:</p>
            <p><a href="{link}" class="btn">View Ticket</a></p>
        </div>
        <div class="email-footer">
            <p>&copy; 2024 Medienscouts | All rights reserved.</p>
        </div>
    </body>
    </html>
    """
)

notify_admin_template = EmailTemplate(
    subject="Admin Notification",
    template_content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; color: #333; padding: 20px; }}
            .email-header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
            .email-content {{ padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); }}
            .btn {{ display: inline-block; padding: 10px 20px; background-color: #007BFF; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
            .email-footer {{ font-size: 12px; color: #777; text-align: center; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="email-header">
            <h1>New Ticket Notification</h1>
        </div>
            <div class="email-content">
                <p>Hello Admin,</p>
                <p>{message}</p>
                <p><a href="{link}" class="btn">View Ticket</a></p>
            </div>
        <div class="email-footer">
            <p>&copy; 2024 Medienscouts | All rights reserved.</p>
        </div>
    </body>
    </html>
    """
)


def send_ticket_link(ticket):
    token = ticket.generate_token()
    link = url_for('view_ticket', token=token, _external=True)
    send_email(ticket_link_template, ticket.email, link=link)


def notify_admin(ticket, ticket_type, message):
    from app.models import User
    admin = User.query.filter_by(role='ADMIN', active=True).first()
    link = url_for('ticket_details', ticket_id=ticket.id, ticket_type=ticket_type, _external=True)
    print(link)
    send_email(notify_admin_template, admin.email, message=message, link=link)
