from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    current_page = "index"
    return render_template("index.j2", current_page=current_page)


@app.route("/о-нас")
@app.post("/feedback")
def feedback():
    # TODO: переписать на flask-wtforms
    # TODO: сделать обработку не xhr-запросов
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")
    newsletter = request.form.get("newsletter")

    # Текст сообщения, который нужно отправить
    newsletter = "Да" if newsletter == "on" else "Нет"
    message = f"""Заполнена форма обратной связи с сайта, данные: \n
    Имя: {name} \n
    Email: {email}\n
    Сообщение: {message}\n
    Подписка на рассылку: {newsletter}\n"""

    # URL для отправки GET-запроса к Telegram API
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    # Параметры запроса
    params = {
        "chat_id": CHAT_ID,
        "text": message
    }

    # Отправка GET-запроса к Telegram API
    response = get(url, params=params, timeout=1000)

    # Проверим успешность запроса
    if response.status_code == 200:
        message = f"{name}, я отправил твою форму" if name else "Я отправил твою форму"
        return jsonify({"status": "success", "message": message}), 200
    return jsonify({"status": "error", "message": "Произошла ошибка."}), 500


def about():
    current_page = "about"
    return render_template("about.j2", current_page=current_page)


@app.route("/контакты")
def contacts():
    current_page = "contacts"
    return render_template("contacts.j2", current_page=current_page)
