import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv

# Carga las variables de entorno que tengo en .env
load_dotenv()

engine= create_engine(os.getenv("DATABASE_URL"))
db =scoped_session(sessionmaker(bind=engine))

### Querys de creacion de las tablas
query_create_users = "CREATE TABLE usuarios(id SERIAL PRIMARY KEY NOT NULL, nombre VARCHAR NOT NULL, apellido VARCHAR NOT NULL, nombre_usuario VARCHAR NOT NULL, hash VARCHAR NOT NULL, correo VARCHAR, numero_telefono INTEGER)"

### Crea las tablas usando las querys
db.execute(query_create_users)

db.commit()

print("Tablas creadas")