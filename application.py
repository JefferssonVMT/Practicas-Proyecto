import os

import requests
from dotenv import load_dotenv
from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, flash, redirect, render_template, request, session
from sqlalchemy.sql.elements import Null
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from flask import jsonify

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")


# Configure session to use filesystem
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    if request.method == "GET":
        return render_template("index.html")

    elif request.method == "POST":

        return "TODO"



@app.route("/register", methods=["GET", "POST"])
def register():
    """Registrar usuario"""
    session.clear()

    if request.method == "GET":
        return render_template("register.html")

    elif request.method == "POST":
        if not request.form.get("nombre_usuario"):
            flash("Debe ingresar el nombre de usuario", "error")
            return render_template("register.html")

        if not request.form.get("correo"):
            flash("Debe ingresar el correo", "error")
            return render_template("register.html")

        elif not request.form.get("password"):
            flash("Debe ingresar la contraseña", "error")
            return render_template("register.html")

        elif not request.form.get("confirmation"):
            flash("Debe confirmar la contraseña", "error")
            return render_template("register.html")

        elif not request.form.get("password") == request.form.get("confirmation"):
            flash("Las contraseñas no coinciden", "error")
            return render_template("register.html")

        if not request.form.get("numero_telefono"):
            flash("Debe ingresar el numero de telefono", "error")
            return render_template("register.html")

        if db.execute(f"SELECT * FROM usuarios WHERE nombre_usuario = '{request.form.get('nombre_usuario')}'").rowcount > 0:
            flash("El usuario ya existe :(", "error")
            return render_template("register.html")

        else:
            password = generate_password_hash(request.form.get("password"))
            db.execute(f"INSERT INTO usuarios (nombre_usuario, correo, hash, numero_telefono) VALUES ('{request.form.get('nombre_usuario')}', '{request.form.get('correo')}', '{password}', '{request.form.get('numero_telefono')}')")
            db.commit()
            flash("Registrado!", "exito")
            return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":

        if not request.form.get("nombre_usuario"):
            flash("Debe ingresar un usuario", "error")
            return render_template("login.html")

        elif not request.form.get("password"):
            flash("Debe ingresar una contraseña", "error")
            return render_template("login.html")

        query = db.execute(f"select * from usuarios WHERE nombre_usuario = '{request.form.get('nombre_usuario')}'").fetchone()

        if not query or not check_password_hash(query['hash'], request.form.get("password")):
            flash("Nombre o contraseña incorrectos", "error")
            return render_template("login.html")

        session["user_id"] = query['id']

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():

    session.clear()

    return redirect("/")

