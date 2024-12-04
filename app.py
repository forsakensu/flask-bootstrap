from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    current_page = "index"
    return render_template("index.j2", current_page=current_page)


@app.route("/о-нас")
def about():
    current_page = "about"
    return render_template("about.j2", current_page=current_page)


@app.route("/контакты")
def contacts():
    current_page = "contacts"
    return render_template("contacts.j2", current_page=current_page)
