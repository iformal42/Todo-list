# TODO : to create TO-DO LIST

"""ENVIRONMENT VARIABLES:-
        * FLASK_KEY
        * DATABASE
        * EMAIL
        * PASSWORD
"""

# modules to download
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Date, Time, Boolean, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user

# inbuild modules
import datetime
from datetime import datetime as dt
import smtplib as sp
from forms import Task, RegisterForm, LoginForm
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')

bootstrap = Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)


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
    is_mail_send: Mapped[Boolean] = mapped_column(Boolean, default=False, nullable=False)

    # user relationship
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="data")

    def send_mail(self, task):
        """this the mail to users if task is due and email not yet send to user for that,
           this function insure the email should send only once """
        if not task.is_mail_send:
            print("send mail")
            my_email = os.environ.get('EMAIL')
            password = os.environ.get('PASSWORD')
            with sp.SMTP("smtp.gmail.com", 587) as connection:
                connection.starttls()
                connection.login(user=my_email, password=password)
                connection.sendmail(
                    from_addr=my_email,
                    to_addrs=task.user.email,
                    msg=f"Subject:Todo is due \n\n "
                        f"Your task '{task.task}' is due. Please complete as soon as possible.  "
                        f"\n Check other todos here https://todo-list-sn98.onrender.com "
                )
            task.is_mail_send = True
            db.session.commit()
            return ""
        else:
            return ""


# user data
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    # Task data
    data = relationship("Tasks", back_populates="user")


with app.app_context():
    db.create_all()


@app.context_processor
def inject_user():
    """This will inject current user detail in every template which is store keyword 'user' """
    return {'user': current_user}


def add_detail(todo: str, schedule, time):
    """Add new task to the data base """
    new_task = Tasks(
        task=todo,
        schedule=schedule,
        time=time,
        is_completed=False,
        user=current_user
    )
    db.session.add(new_task)
    db.session.commit()


def check_time():
    """Returns current date and time """
    today = dt.now()
    current_date = today.date()
    current_time = today.time()
    return current_date, current_time


@app.route("/")
def home():
    if current_user.is_authenticated:
        # fetch pending tasks
        pending_task = db.session.execute(
            db.select(Tasks).where(Tasks.is_completed.is_(False) & (Tasks.user_id == current_user.id)).
            order_by(Tasks.id)).scalars()
        # fetch completed tasks
        completed_task = db.session.execute(
            db.select(Tasks).where(Tasks.is_completed.is_(True) & (Tasks.user_id == current_user.id)).
            order_by(Tasks.id)).scalars()
    else:
        return render_template('index.html')

    # current time and date
    now_date, now_time = check_time()
    return render_template('index.html', detail=pending_task, completed_task=completed_task,
                           current_date=now_date, current_time=now_time)


@app.route("/add-task", methods=["POST", "GET"])
def task():
    """This function use for adding new task  """
    form = Task()
    if current_user.is_authenticated:
        if form.validate_on_submit():
            todo = form.task.data
            schedule = form.schedule.data
            timer = form.time.data

            if schedule and timer is None:
                # default time if user add date
                timer = datetime.time(hour=23, minute=59)

            add_detail(todo, schedule, timer)
            return redirect(url_for("home"))
        return render_template("task.html", form=form)
    else:
        flash('Your not login!')
        return redirect(url_for('home'))


@app.route("/mark/<int:id>", methods=["POST", "GET"])
def completed(id):
    """This function runs which check box is clicked in home page """
    task = db.get_or_404(Tasks, id)
    task.is_completed = True
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete/<int:id>")
def delete(id):
    """This function delete the task when user click on delete or trash-can """
    task = db.get_or_404(Tasks, id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("home"))


@app.route('/signup', methods=["POST", "GET"])
def signup():
    """This manage signup page """
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        user_exits = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user_exits:
            flash("you've already sign up with this email")
            return redirect(url_for("login"))

        password = form.password.data
        hash_pass = generate_password_hash(password=password, method="pbkdf2", salt_length=9)
        new_user = User(email=email, name=name, password=hash_pass)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("signup.html", form=form)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.route('/login', methods=["POST", "GET"])
def login():
    """this manage login Page"""
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        pwd = form.password.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user:
            flash("not a valid email")
            return redirect(url_for("login"))
        elif check_password_hash(user.password, pwd):
            login_user(user)
            # return render_template("index.html",login=True)
            return redirect(url_for("home"))
        else:
            flash("invalid password")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    """Logout"""
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
