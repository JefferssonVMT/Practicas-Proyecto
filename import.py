import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv

# Carga las variables de entorno que tengo en .env
load_dotenv()

engine= create_engine(os.getenv("DATABASE_URL"))
db =scoped_session(sessionmaker(bind=engine))

# Querys de creacion de las tablas
query_create_users = "CREATE TABLE usuarios(id SERIAL PRIMARY KEY NOT NULL, nombre VARCHAR NOT NULL, apellido VARCHAR NOT NULL, nombre_usuario VARCHAR NOT NULL, hash VARCHAR NOT NULL, correo VARCHAR, numero_telefono INTEGER, activo BOOLEAN NOT NULL)"
query_create_category = "CREATE TABLE categorias(id SERIAL PRIMARY KEY NOT NULL, nombre VARCHAR NOT NULL)"
query_create_posts = "CREATE TABLE publicaciones(id SERIAL PRIMARY KEY NOT NULL, titulo VARCHAR NOT NULL, descripcion VARCHAR NOT NULL, imagen1 VARCHAR NOT NULL, imagen2 VARCHAR, disponible BOOLEAN NOT NULL, id_user INTEGER REFERENCES usuarios, id_categoria INTEGER REFERENCES categorias)"
query_create_reseñas = "CREATE TABLE reseñas(id SERIAL PRIMARY KEY NOT NULL, comentario VARCHAR, user_id INTEGER REFERENCES usuarios, publicacion_id INTEGER REFERENCES publicaciones)"

db.execute(query_create_users)
db.execute(query_create_category)
db.execute(query_create_posts)
db.execute(query_create_reseñas)

categorias = ("Ropa y accesorios","Electrónica","Familia","Hogar y jardín","Vehículos","Clasificados","Ofertas","Entretenimiento","Pasatiempos","Vivienda")

for cat in categorias:
    db.execute(f"insert into categorias (nombre) values ('{cat}')")

db.commit()

print("Tablas creadas")
