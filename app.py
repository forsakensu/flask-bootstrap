from os import getenv

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from requests import get
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from wtforms import BooleanField, EmailField, StringField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, Length

app = Flask(__name__)

load_dotenv()

REQUEST_TIMEOUT = 1000
STATUS_OK = 200
STATUS_ERROR = 500
TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = getenv("CHAT_ID")

# Конфигурация приложения
app.config["SECRET_KEY"] = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("CONNECTION_DB")


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
bcrypt = Bcrypt()

db.init_app(app)
migrate.init_app(app, db)
bcrypt.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"



@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
    # return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    email: Mapped[str]
    phone: Mapped[str]


class Feedback(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey(User.id))
    name: Mapped[str]
    email: Mapped[str]
    message: Mapped[str]
    newsletter: Mapped[str]


@app.get("/")
def index():
    db.create_all()
    current_page = "index"
    return render_template("index.j2", current_page=current_page)


class FeedbackForm(FlaskForm):
    name = StringField("Имя", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    message = TextAreaField("Сообщение", validators=[Length(max=500)])
    newsletter = BooleanField("Подписка на рассылку")
    submit = SubmitField("Отправить")


class RegistrationForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6)])
    first_name = StringField("Имя", validators=[DataRequired()])
    last_name = StringField("Фамилия", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Телефон", validators=[Length(max=20)])
    submit = SubmitField("Зарегистрироваться")

class LoginForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])


@app.post("/feedback")
def feedback():
    if request.is_json:
        form = request.json

        name = form["name"]
        email = form["email"]
        message_content = form["message"]
        newsletter_boolean = bool(form.get("newsletter"))
    else:
        form = FeedbackForm()

        name = form.name.data
        email = form.email.data
        message_content = form.message.data
        newsletter_boolean = form.newsletter.data == "on"

    feedback_db = Feedback(
        name=name, email=email, message=message_content, newsletter=newsletter_boolean, user_id=current_user.id
    )
    db.session.add(feedback_db)
    db.session.commit()

    # Текст сообщения, который нужно отправить
    newsletter = "Да" if newsletter_boolean else "Нет"
    message = f"""Заполнена форма обратной связи с сайта, данные: \n
    Имя: {name} \n
    Email: {email}\n
    Сообщение: {message_content}\n
    Подписка на рассылку: {newsletter}\n"""

    # URL для отправки GET-запроса к Telegram API
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Параметры запроса
    params = {"chat_id": CHAT_ID, "text": message}

    # Отправка GET-запроса к Telegram API
    response = get(url, params=params, timeout=REQUEST_TIMEOUT)

    # Проверим успешность запроса
    if response.status_code == STATUS_OK:
        if not request.is_json:
            return redirect(url_for("confirm"))
        message = f"{name}, я отправил твою форму" if name else "Я отправил твою форму"
        return jsonify({"status": "success", "message": message}), STATUS_OK
    if request.is_json:
        return jsonify({"status": "error", "message": "Произошла ошибка."}), STATUS_ERROR
    return render_template("error.j2"), STATUS_ERROR


@app.get("/о-нас")
def about():
    current_page = "about"
    return render_template("about.j2", current_page=current_page)


@app.get("/контакты")
@login_required
def contacts():
    form = FeedbackForm()
    current_page = "contacts"
    return render_template("contacts.j2", current_page=current_page, form=form)


@app.get("/спасибо")
def confirm():
    current_page = "confirm"
    return render_template("confirm.j2", current_page=current_page)


@app.get("/обратная-связь")
@login_required
def form_results():
    feedbacks_db = db.session.execute(db.select(Feedback).order_by(Feedback.id)).scalars()
    return render_template("form-results.j2", feedbacks=feedbacks_db)


@app.route("/register", methods=["GET", "POST"])
def register():
    reg_form = RegistrationForm()
    if request.method == "POST":
        username = reg_form.username.data
        existing_user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        if existing_user:
            return render_template("register.j2", form=reg_form)
        password = bcrypt.generate_password_hash(reg_form.password.data).decode("utf-8")
        new_user = User(
            username=username,
            password=password,
            first_name=reg_form.first_name.data,
            last_name=reg_form.last_name.data,
            email=reg_form.email.data,
            phone=reg_form.phone.data,
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.j2", form=reg_form)



@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if request.method == "POST":
        username = login_form.username.data
        password = login_form.password.data
        # TODO: переписать на новый синтаксис
        user = db.session.query(User).filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("form_results"))
        return "Неправильный логин или пароль!"
    return render_template("login.j2", form=login_form)



@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
