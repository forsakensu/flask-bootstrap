from os import getenv

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, redirect
from flask_wtf import FlaskForm
from requests import get
from wtforms import StringField, SubmitField, EmailField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length

app = Flask(__name__)

load_dotenv()

TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = getenv("CHAT_ID")
app.secret_key = 'dev'

@app.get("/")
def index():
    current_page = "index"
    return render_template("index.j2", current_page=current_page)


class FeedbackForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Сообщение', validators=[Length(max=500)])
    newsletter = BooleanField('Подписка на рассылку')
    submit = SubmitField('Отправить')

@app.post("/feedback")
def feedback():
    # TODO: переписать на flask-wtforms
    # TODO: сделать обработку не xhr-запросов

    form = FeedbackForm()

    name = form.name.data
    email = form.email.data
    message_content = form.message.data
    newsletter = "Да" if form.newsletter.data else "Нет"

    # Текст сообщения, который нужно отправить
    newsletter = "Да" if newsletter == "on" else "Нет"
    message = f"""Заполнена форма обратной связи с сайта, данные: \n
    Имя: {name} \n
    Email: {email}\n
    Сообщение: {message_content}\n
    Подписка на рассылку: {newsletter}\n"""

    # URL для отправки GET-запроса к Telegram API
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Параметры запроса
    params = {
        "chat_id": CHAT_ID,
        "text": message
    }

    # Отправка GET-запроса к Telegram API
    response = get(url, params=params, timeout=1000)

    # Проверим успешность запроса
    if response.status_code == 200:
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            return redirect("/confirm")
        message = f"{name}, я отправил твою форму" if name else "Я отправил твою форму"
        return jsonify({"status": "success", "message": message}), 200
    return jsonify({"status": "error", "message": "Произошла ошибка."}), 500


@app.get("/о-нас")
def about():
    current_page = "about"
    return render_template("about.j2", current_page=current_page)


@app.get("/контакты")
def contacts():
    form = FeedbackForm()
    current_page = "contacts"
    return render_template("contacts.j2", current_page=current_page, form=form)

@app.get("/confirm")
def confirm():
    current_page = "confirm"
    return render_template("confirm.j2", current_page=current_page)
