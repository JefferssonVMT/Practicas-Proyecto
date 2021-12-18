import os
from re import search
from dotenv import load_dotenv
from flask import Flask, json, session
from flask.scaffold import _matching_loader_thinks_module_is_package
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from werkzeug.utils import secure_filename
from flask_babel import Babel, gettext

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["BABEL_DEFAULT_LOCALE"] = "es"

Session(app)
babel = Babel(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@babel.localeselector
def get_locale():
    if session.get("lang") is None:
        session["lang"] = "es"
    
    return session["lang"]
    #return request.accept_languages.best_match(['es', 'en'])

@app.route("/lang")
@login_required
def lang():
    if session["lang"] ==  "es":
        session["lang"] = "en"

    elif session["lang"] == "en":
        session["lang"] = "es"

    return  {"nuevo lenguaje": session["lang"]}

@app.route("/", methods=["GET"])
@login_required
def index():
    session['index'] = db.execute("SELECT p.id, u.activo FROM publicaciones p INNER JOIN usuarios u ON p.id_user = u.id WHERE u.activo = true AND p.disponible = true").rowcount
    print(session['index'])
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

        if len(request.form.get("telefono")) > 8:
            flash("Telefono invalido o formato incorrecto", "error")
            return render_template("register.html", error = "telefono")

        if db.execute(f"SELECT * FROM usuarios WHERE nombre_usuario = '{request.form.get('nombre_usuario')}'").rowcount > 0:
            flash("El usuario ya existe", "error")
            return render_template("register.html", error = "username")

        else:
            password = generate_password_hash(request.form.get("password"))

            if not correo and numero_telefono:
                db.execute(f"INSERT INTO usuarios (nombre, apellido, nombre_usuario, hash, numero_telefono, activo) VALUES ('{request.form.get('nombre')}','{request.form.get('apellido')}', '{request.form.get('nombre_usuario')}', '{password}', {numero_telefono}, TRUE)")
                db.commit()

            elif not numero_telefono and correo:
                db.execute(f"INSERT INTO usuarios (nombre, apellido, nombre_usuario, hash, correo, activo) VALUES ('{request.form.get('nombre')}','{request.form.get('apellido')}', '{request.form.get('nombre_usuario')}', '{password}', '{correo}', TRUE)")
                db.commit()

            elif not numero_telefono and not correo:
                db.execute(f"INSERT INTO usuarios (nombre, apellido, nombre_usuario, hash, activo) VALUES ('{request.form.get('nombre')}','{request.form.get('apellido')}', '{request.form.get('nombre_usuario')}', '{password}', TRUE)")
                db.commit()

            else:
                db.execute(f"INSERT INTO usuarios (nombre, apellido, nombre_usuario, hash, correo, numero_telefono, activo) VALUES ('{request.form.get('nombre')}','{request.form.get('apellido')}', '{request.form.get('nombre_usuario')}', '{password}', '{correo}', {numero_telefono}, TRUE)")
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
            return render_template("login.html", error = "password")

        session["user_id"] = query['id']

        if query['activo'] == False:
            db.execute(f"UPDATE usuarios SET activo = true WHERE id = {session['user_id']}")
            db.commit()
            flash(f"Bienvenid@ nuevamente {query['nombre']}")
            return redirect("/")
        
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
    publicaciones =  db.execute(f"SELECT id, titulo, descripcion FROM publicaciones WHERE id_user = {session['user_id']} AND disponible = true ORDER BY id DESC")

    if request.method == "GET":
        return render_template("micuenta.html", usuario = usuario, publicaciones = publicaciones)

    elif request.method == "POST":
        info = db.execute(f"SELECT * FROM usuarios WHERE id = {session['user_id']}").fetchone()

        if request.form.get('phone') == str(info[6]):
            flash("El nuevo numero de telefono debe ser distinto al anterior", "error")
            return render_template("micuenta.html", usuario = usuario, publicaciones = publicaciones)

        elif request.form.get('phone') and not request.form.get('phone').isdigit():
            flash("Telefono invalido o con formmato incorrecto", "error")
            return render_template("micuenta.html", usuario = usuario, error = "phone", publicaciones = publicaciones)

        elif request.form.get('phone') and len(request.form.get("phone")) > 8:
            flash("Telefono invalido o con formmato incorrecto", "error")
            return render_template("micuenta.html", usuario = usuario, error = "phone", publicaciones = publicaciones)

        elif not request.form.get('phone') and request.form.get('correo'):
            db.execute(f"UPDATE usuarios SET correo = '{request.form.get('correo')}' WHERE id = {session['user_id']}")
            db.commit()

        elif not request.form.get('correo') and request.form.get('phone'):
            db.execute(f"UPDATE usuarios SET numero_telefono = {request.form.get('phone')} WHERE id = {session['user_id']}")
            db.commit()

        elif request.form.get('phone') and request.form.get('correo'):
            db.execute(f"UPDATE usuarios SET correo = '{request.form.get('correo')}', numero_telefono = {request.form.get('phone')} WHERE id = {session['user_id']}")
            db.commit()

        else:
            flash("Nada que editar", "error")
            return render_template("micuenta.html", usuario = usuario, publicaciones = publicaciones)

        flash("Cambios realizados", "exito")

        return redirect("/micuenta")

@app.route("/nuevapublicacion", methods=["GET", "POST"])
@login_required
def nuevapublicacion():
    row = db.execute("SELECT nombre FROM categorias")

    categorias = []

    if session['lang'] == 'es':
        for cat in row:
            categorias.append(cat[0])
    elif session['lang'] == 'en':
        for cat in row:
            categorias.append(gettext(cat[0]))

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
            return render_template("nuevapublicacion.html", categorias = categorias)

        archivo = open("static/diccionario.txt").read()
        print(archivo)
        
        for palabra in titulo.split():
            if palabra in archivo:
                flash("No esta permitido el vocabulario vulgar, ofensivo o polemico...", "error")
                return render_template("nuevapublicacion.html", categorias = categorias)

        for palabra in descripcion.split():
            if palabra in archivo:
                flash("No esta permitido el vocabulario vulgar, ofensivo o polemico...", "error")
                return render_template("nuevapublicacion.html", categorias = categorias)

        if not imagen1 and not imagen2:
            flash("Se requiere subir almenos una imagen", "error")
            return render_template("nuevapublicacion.html", categorias = categorias)

        elif imagen1 and not imagen2 and titulo and descripcion and categoria:
            imagen1.save(os.path.join(basepath, f'static//posts//users_id//{iddd}//imagenes', secure_filename(imagen1.filename)))
            rutaImagen1 = f'static//posts//users_id//{iddd}//imagenes//' + imagen1.filename

            cat = db.execute(f"SELECT id from categorias WHERE nombre = '{categoria}'").fetchone()[0]

            db.execute(f"INSERT INTO publicaciones (titulo, descripcion, id_categoria, imagen1, disponible, id_user) values ('{titulo}', '{descripcion}', '{cat}', '{rutaImagen1}', True, '{session['user_id']}')")
            db.commit()

            flash("Publicado exitosamente")
            return redirect("/")

        elif imagen2 and not imagen1 and titulo and descripcion and categoria:
            imagen2.save(os.path.join(basepath, f'static//posts//users_id//{iddd}//imagenes', secure_filename(imagen2.filename)))
            rutaImagen2 = f'static//posts//users_id//{iddd}//imagenes//' + imagen2.filename

            cat = db.execute(f"SELECT id from categorias WHERE nombre = '{categoria}'").fetchone()[0]

            db.execute(f"INSERT INTO publicaciones (titulo, descripcion, id_categoria, imagen1, id_user, disponible) values ('{titulo}', '{descripcion}', '{cat}', '{rutaImagen2}', '{session['user_id']}', True)")
            db.commit()

            flash("Publicado exitosamente")
            return redirect("/")

        elif imagen1 and imagen2 and titulo and descripcion and categoria:
            imagen1.save(os.path.join(basepath, f'static//posts//users_id//{iddd}//imagenes', secure_filename(imagen1.filename)))
            imagen2.save(os.path.join(basepath, f'static//posts//users_id//{iddd}//imagenes', secure_filename(imagen2.filename)))
            rutaImagen1 = f'static//posts//users_id//{iddd}//imagenes//' + imagen1.filename
            rutaImagen2 = f'static//posts//users_id//{iddd}//imagenes//' + imagen2.filename

            cat = db.execute(f"SELECT id from categorias WHERE nombre = '{categoria}'").fetchone()[0]

            db.execute(f"INSERT INTO publicaciones (titulo, descripcion, id_categoria, imagen1, imagen2, id_user, disponible) values ('{titulo}', '{descripcion}', '{cat}', '{rutaImagen1}', '{rutaImagen2}', '{session['user_id']}', True)")
            db.commit()

            flash("Publicado exitosamente")
            return redirect("/")


@app.route("/cargar_mas")
@login_required
def cargar_mas():
    #publicaciones = db.execute(f"SELECT p.id as pid, p.titulo, p.descripcion, p.imagen1, p.disponible, u.nombre_usuario as user, u.activo FROM publicaciones p INNER JOIN usuarios u ON p.id_user = u.id WHERE u.activo = true AND p.disponible = true AND p.id > {session['index']} ORDER BY p.id DESC LIMIT 2")
    consulta  = f"SELECT p.id as pid, p.titulo, p.descripcion, p.imagen1, p.disponible, u.nombre_usuario as user, u.activo FROM publicaciones p INNER JOIN usuarios u ON p.id_user = u.id WHERE u.activo = true AND p.disponible = true AND p.id <= {session['index']} ORDER BY p.id DESC LIMIT 12"
    publicaciones = db.execute(consulta)
    if session['index'] > 0:
        session['index'] -= 10

    data = []

    print(consulta)
    for xd in publicaciones:
        data.append(dict(xd))
        print(xd)

    print(session['index'])
    return jsonify(data)

@app.route("/desactivar_cuenta")
@login_required
def desactivar_cuenta():
    db.execute(f"UPDATE usuarios SET activo = false WHERE id = {session['user_id']}")
    db.commit()
    session.clear()
    flash("Cuenta desactivada correctamente", "exito")
    return render_template("login.html")


@app.route("/detalles", methods = ["GET", "POST"])
@login_required
def info():
    id = request.args.get('id', type = int)

    if not id or id <= 0:
        flash("Ha ocurrido un error buscando la publicacion", "error")
        return render_template("index.html")

    publicaciones = db.execute(f"SELECT p.id as pid, p.titulo, p.descripcion, p.imagen1, p.imagen2, p.id_user, u.nombre_usuario as user, u.numero_telefono as numero, u.correo as correo FROM publicaciones p INNER JOIN usuarios u ON p.id_user = u.id where p.id = {id}").fetchone()

    comentarios = db.execute(f"SELECT comentario, nombre_usuario FROM reseñas r INNER JOIN usuarios u ON r.user_id = u.id WHERE publicacion_id = {id}")

    if request.method == "GET":
        return render_template("detalles.html", publicaciones = publicaciones, comentarios = comentarios, id = id)

    else:
        db.execute("insert into reseñas (publicacion_id, comentario, user_id) values (:publicacion_id, :comentario, :user_id)",
            {"publicacion_id": id, "comentario": request.form.get("comentario"), "user_id": session['user_id']})
        db.commit()

        return redirect(f"detalles?id={id}")

@app.route("/vendido")
def vendido():
    id  = request.args.get('id', type=int)

    row = db.execute(f"SELECT * FROM publicaciones WHERE id = {id} AND id_user = {session['user_id']}")

    if not vendido or not row:
        return  "Solicitud invalida", 400

    db.execute(f"UPDATE publicaciones SET disponible = false WHERE id = {id} AND id_user = {session['user_id']}")
    db.commit()

    return {'id de producto': f'{id}', 'vendido': 'true'}, 200


@app.route("/search")
def search():
    q = request.args.get('q')
    cat_id = request.args.get('id_categoria', type = int)

    if q and not cat_id:
        consulta  = f"SELECT p.id as pid, p.titulo, p.descripcion, p.imagen1, p.disponible, u.nombre_usuario as user, u.activo FROM publicaciones p INNER JOIN usuarios u ON p.id_user = u.id WHERE u.activo = true AND p.disponible = true AND (UPPER(p.titulo) LIKE UPPER(:q) OR UPPER(p.descripcion) LIKE UPPER(:q) or UPPER(u.nombre_usuario) LIKE UPPER(:q)) ORDER BY p.id DESC LIMIT 15"
        publicaciones = db.execute(consulta, {'q': '%{}%'.format(q)})

        data = []

        for xd in publicaciones:
            data.append(dict(xd))

        return jsonify(data)

    elif cat_id and not q:
        consulta  = f"SELECT p.id as pid, p.titulo, p.descripcion, p.imagen1, p.disponible, p.id_categoria, u.nombre_usuario as user, u.activo FROM publicaciones p INNER JOIN usuarios u ON p.id_user = u.id WHERE u.activo = true AND p.disponible = true AND p.id_categoria = {cat_id} ORDER BY p.id DESC LIMIT 15"
        publicaciones = db.execute(consulta)

        data = []

        for xd in publicaciones:
            data.append(dict(xd))
            print(xd)

        return jsonify(data)
    