# TODO : to create TO-DO LIST
import datetime

from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Date, Time, Boolean, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required

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

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="data")


# user data
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    data = relationship("Tasks", back_populates="user")


with app.app_context():
    db.create_all()


def add_detail(todo: str, schedule, time):
    new_task = Tasks(
        task=todo,
        schedule=schedule,
        time=time,
        is_completed=False,
        user=current_user
    )
    db.session.add(new_task)
    db.session.commit()


@app.route("/")
def home():
    if current_user.is_authenticated:
        user_login = True
        pending_task = db.session.execute(
            db.select(Tasks).where(Tasks.is_completed.is_(False) & (Tasks.user_id == current_user.id)).order_by(Tasks.id)).scalars()
        completed_task = db.session.execute(
            db.select(Tasks).where(Tasks.is_completed.is_(True) & (Tasks.user_id == current_user.id)).order_by(Tasks.id)).scalars()
    else:
        user_login = False
        return render_template('index.html', login=user_login)

    return render_template('index.html', detail=pending_task, completed_task=completed_task,
                           login=user_login)


@app.route("/add-task", methods=["POST", "GET"])
def task():
    form = Task()
    if current_user.is_authenticated:
        if form.validate_on_submit():
            todo = form.task.data
            schedule = form.schedule.data
            timer = form.time.data
            if schedule and timer is None:
                timer = datetime.time(hour=23, minute=59)
            add_detail(todo, schedule, timer)
            return redirect(url_for("home"))
        return render_template("task.html", form=form)
    else:
        flash('Your not login!')
        return redirect(url_for('home'))

@app.route("/mark/<int:id>", methods=["POST", "GET"])
def completed(id):
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


@app.route('/signup', methods=["POST", "GET"])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        user_exits = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user_exits:
            flash("you've already sign up with this email")
            return redirect(url_for("login"))
        #
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
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
