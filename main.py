# TODO : to create TO-DO LIST
import datetime

from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap5
from forms import Task
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Date, Time, Boolean
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
bootstrap = Bootstrap5(app)


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE')

db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Tasks(db.Model):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task: Mapped[str] = mapped_column(String(250), nullable=False)
    schedule: Mapped[Date] = mapped_column(Date, nullable=True)
    time: Mapped[Time] = mapped_column(Time, nullable=True)
    is_completed: Mapped[Boolean] = mapped_column(Boolean, nullable=False)


with app.app_context():
    db.create_all()


def add_detail(todo: str, schedule, time):
    new_task = Tasks(
        task=todo,
        schedule=schedule,
        time=time,
        is_completed=False
    )
    db.session.add(new_task)
    db.session.commit()


@app.route("/")
def home():
    pending_task = db.session.execute(
        db.select(Tasks).where(Tasks.is_completed == False).order_by(Tasks.id)).scalars().all()
    completed_task = db.session.execute(
        db.select(Tasks).where(Tasks.is_completed == "true").order_by(Tasks.id)).scalars().all()
    return render_template('index.html', detail=pending_task, completed_task=completed_task)


@app.route("/add-task", methods=["POST", "GET"])
def task():
    form = Task()
    if form.validate_on_submit():
        todo = form.task.data
        schedule = form.schedule.data
        timer = form.time.data
        if schedule and timer is None:
            timer = datetime.time(hour=23, minute=59)
        add_detail(todo, schedule, timer)
        return redirect(url_for("home"))
    return render_template("task.html", form=form)


@app.route("/mark/<int:id>", methods=["POST", "GET"])
def completed(id):
    print(id)
    task = db.get_or_404(Tasks, id)
    task.is_completed = True
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete.<int:id>")
def delete(id):
    task = db.get_or_404(Tasks, id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
    # a ,b= None,None
    # if not a and not b:
    #     print("none", a)
    # else:
    #     print("not none")
