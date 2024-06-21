from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField,TimeField,RadioField
from wtforms.validators import DataRequired,Optional


class Task(FlaskForm):
    task = StringField("Enter Task", validators=[DataRequired()])
    schedule = DateField("schedule", validators=[Optional()])
    time = TimeField("set time", validators=[Optional()])
    submit = SubmitField("Submit Post")


class Complete(FlaskForm):
    checkbox = RadioField()