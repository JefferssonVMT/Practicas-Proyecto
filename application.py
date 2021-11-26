import os
from dotenv import load_dotenv
from flask import Flask, json, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from werkzeug.utils import secure_filename

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

@app.route("/", methods=["GET"])
@login_required
def index():
    session['ids'] = []
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Registrar usuario"""
    session.clear()

    if request.method == "GET":
        return render_template("register.html")

    elif request.method == "POST":

        correo = request.form.get("correo")
        numero_telefono = request.form.get("telefono")

        if not request.form.get("password") == request.form.get("confirmation"):
            flash("Las contraseñas no coinciden", "error")
            return render_template("register.html", error = "confirmation")

        if not request.form.get("nombre_usuario") or not request.form.get("nombre") or not request.form.get("apellido"):
            flash("Datos invalidos o vacios", "error")
            return render_template("register.html", error = "nombre")

        if request.form.get("telefono") and not request.form.get("telefono").isdigit():
            flash("Telefono invalido o formato incorrecto", "error")
            return render_template("register.html", error = "telefono")

        if db.execute(f"SELECT * FROM usuarios WHERE nombre_usuario = '{request.form.get('nombre_usuario')}'").rowcount > 0:
            flash("El usuario ya existe", "error")
            return render_template("register.html", error = "username")

        else:
            password = generate_password_hash(request.form.get("password"))

            if not correo and numero_telefono:
                db.execute(f"INSERT INTO usuarios (nombre, apellido, nombre_usuario, hash, numero_telefono) VALUES ('{request.form.get('nombre')}','{request.form.get('apellido')}', '{request.form.get('nombre_usuario')}', '{password}', '{numero_telefono}')")
                db.commit()

            elif not numero_telefono and correo:
                db.execute(f"INSERT INTO usuarios (nombre, apellido, nombre_usuario, hash, correo) VALUES ('{request.form.get('nombre')}','{request.form.get('apellido')}', '{request.form.get('nombre_usuario')}', '{password}', '{correo}')")
                db.commit()

            elif not numero_telefono and not correo:
                db.execute(f"INSERT INTO usuarios (nombre, apellido, nombre_usuario, hash) VALUES ('{request.form.get('nombre')}','{request.form.get('apellido')}', '{request.form.get('nombre_usuario')}', '{password}')")
                db.commit()

            else:
                db.execute(f"INSERT INTO usuarios (nombre, apellido, nombre_usuario, hash, correo, numero_telefono) VALUES ('{request.form.get('nombre')}','{request.form.get('apellido')}', '{request.form.get('nombre_usuario')}', '{password}', '{correo}'', '{numero_telefono}')")
                db.commit()

            id = db.execute(f"SELECT id FROM usuarios WHERE nombre_usuario= '{request.form.get('nombre_usuario')}'").fetchone()["id"]

            # Remember which user has logged in
            session["user_id"] = id

            os.makedirs(f'static/posts/users_id/{id}/imagenes', exist_ok=True)

            flash("Registrado!", "exito") 
            return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":
        
        if not request.form.get('nombre_usuario'):
            flash("Debe ingresar el correo nombre de usuario", "error")
            return render_template("login.html", error = "username")
        
        elif not request.form.get('password'):
            flash("Debe ingresar la contraseña", "error")
            return render_template("login.html", error = "password")

        query = db.execute(f"select * from usuarios WHERE nombre_usuario = '{request.form.get('nombre_usuario')}' or correo = '{request.form.get('nombre_usuario')}'").fetchone()

        if not query or not check_password_hash(query['hash'], request.form.get("password")):
            flash("Nombre o contraseña incorrectos", "error")
            return render_template("login.html")

        session["user_id"] = query['id']

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/actualizarcontraseña", methods=["GET", "POST"])
@login_required
def cambiarcontraseña():
    if request.method == "GET":
        return render_template("actualizarcontraseña.html")

    elif request.method == "POST":
        newpassword = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validar que password y confirmation tengan los mismos valores
        if newpassword != confirmation:
            flash("Las contraseñas no coindicen", "error")
            return render_template("actualizarcontraseña.html", error = "confirmation")
        
        elif not newpassword and not confirmation:
            flash("Debe ingresar los datos", "error")
            return render_template("actualizarcontraseña.html", error = "password")

        # Ingresar los datos a la base de datos
        else:

            password = generate_password_hash(newpassword)
            db.execute(f"UPDATE usuarios SET hash = '{password}' WHERE id = {session['user_id']}")
            db.commit()
            flash("Contraseña actualizada", "exito")

            # Redireccionar al index
            return redirect("/")


@app.route("/logout")
@login_required
def logout():

    session.clear()

    return redirect("/")

@app.route("/micuenta", methods=["GET", "POST"])
@login_required
def micuenta():
    
    usuario = db.execute(f"SELECT * FROM usuarios WHERE id = {session['user_id']}")

    if request.method == "GET":
        return render_template("micuenta.html", usuario = usuario)

    elif request.method == "POST":

        if request.form.get('phone') and not request.form.get('phone').isdigit():
            flash("Telefono invalido o con formmato incorrecto", "error")
            return render_template("micuenta.html", usuario = usuario, error = "phone")

        if not request.form.get('phone') and request.form.get('mail'):
            db.execute(f"UPDATE usuarios SET correo = '{request.form.get('mail')}' WHERE id = {session['user_id']}")
            db.commit()

        elif not request.form.get('mail') and request.form.get('phone'):
            db.execute(f"UPDATE usuarios SET numero_telefono = '{request.form.get('phone')}' WHERE id = {session['user_id']}")
            db.commit()

        elif request.form.get('phone') and request.form.get('mail'):
            db.execute(f"UPDATE usuarios SET correo = '{request.form.get('mail')}', '{request.form.get('phone')}' WHERE id = {session['user_id']}")
            db.commit()

        else:
            flash("Nada que editar", "error")
            return render_template("micuenta.html", usuario = usuario)

        flash("Cambios realizados", "exito")

        return redirect("/micuenta")

@app.route("/nuevapublicacion", methods=["GET", "POST"])
@login_required
def nuevapublicacion():        
    row = db.execute("SELECT nombre FROM categorias")

    categorias = []

    for cat in row:
        categorias.append(cat[0])

    if request.method == "GET":
        
        return render_template("nuevapublicacion.html", categorias = categorias)

    else:
        iddd = session["user_id"]
        basepath = os.path.dirname(__file__)

        imagen1 = request.files['imagen1']
        imagen2 = request.files['imagen2']

        titulo = request.form.get("titulo")
        descripcion = request.form.get("nota")
        categoria = request.form.get("categoria")

        rutaImagen1 = None
        rutaImagen2 = None

        if not titulo or not descripcion or not categoria:
            flash("Debe introducir todos campos de texto solicitados", "error")
            return render_template("nuevapublicacion.html")

        elif not imagen1 and not imagen2:
            flash("Se requiere subir almenos una imagen", "error")
            return render_template("nuevapublicacion.html")

        elif imagen1 and not imagen2 and titulo and descripcion and categoria:
            imagen1.save(os.path.join(basepath, f'static\\posts\\users_id\\{iddd}\\imagenes', secure_filename(imagen1.filename)))
            rutaImagen1 = f'static\\posts\\users_id\\{iddd}\\imagenes\\' + imagen1.filename

            cat = db.execute(f"SELECT id from categorias WHERE nombre = '{categoria}'").fetchone()[0]

            db.execute(f"INSERT INTO publicaciones (titulo, descripcion, id_categoria, imagen1, id_user) values ('{titulo}', '{descripcion}', '{cat}', '{rutaImagen1}', '{session['user_id']}')")
            db.commit()

            flash("Publicado exitosamente")
            return redirect("/")

        elif imagen2 and not imagen1 and titulo and descripcion and categoria:
            imagen2.save(os.path.join(basepath, f'static\\posts\\users_id\\{iddd}\\imagenes', secure_filename(imagen2.filename)))
            rutaImagen2 = f'static\\posts\\users_id\\{iddd}\\imagenes\\' + imagen2.filename

            cat = db.execute(f"SELECT id from categorias WHERE nombre = '{categoria}'").fetchone()[0]

            db.execute(f"INSERT INTO publicaciones (titulo, descripcion, id_categoria, imagen1, id_user) values ('{titulo}', '{descripcion}', '{cat}', '{rutaImagen2}', '{session['user_id']}')")
            db.commit()

            flash("Publicado exitosamente")
            return redirect("/")

        elif imagen1 and imagen2 and titulo and descripcion and categoria:
            imagen1.save(os.path.join(basepath, f'static\\posts\\users_id\\{iddd}\\imagenes', secure_filename(imagen1.filename)))
            imagen2.save(os.path.join(basepath, f'static\\posts\\users_id\\{iddd}\\imagenes', secure_filename(imagen2.filename)))
            rutaImagen1 = f'static\\posts\\users_id\\{iddd}\\imagenes\\' + imagen1.filename
            rutaImagen2 = f'static\\posts\\users_id\\{iddd}\\imagenes\\' + imagen2.filename

            cat = db.execute(f"SELECT id from categorias WHERE nombre = '{categoria}'").fetchone()[0]

            db.execute(f"INSERT INTO publicaciones (titulo, descripcion, id_categoria, imagen1, imagen2, id_user) values ('{titulo}', '{descripcion}', '{cat}', '{rutaImagen1}', '{rutaImagen2}', '{session['user_id']}')")
            db.commit()

            flash("Publicado exitosamente")
            return redirect("/")


@app.route("/cargar_mas")
def cargar_mas():
    publicaciones = db.execute("SELECT * FROM publicaciones p INNER JOIN usuarios u ON p.id_user = u.id ORDER BY p.id DESC LIMIT 15")
    
    data = []

    for xd in publicaciones:
        data.append(dict(xd))

    return jsonify(data)