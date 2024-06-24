from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, TimeField
from wtforms.validators import DataRequired, Optional


class Task(FlaskForm):
    task = StringField("Enter Task", validators=[DataRequired()])
    schedule = DateField("schedule", validators=[Optional()])
    time = TimeField("set time", validators=[Optional()])
    submit = SubmitField("Submit Post")


# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign up")


# TODO: Create a LoginForm to login existing users

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField(" Log in")
