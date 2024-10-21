from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.fields.datetime import DateField, TimeField, DateTimeField
from wtforms.fields.list import FieldList
from wtforms.fields.simple import PasswordField
from wtforms.validators import DataRequired, Email



class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Post')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')