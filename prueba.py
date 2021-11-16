import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv

# Carga las variables de entorno que tengo en .env
load_dotenv()

engine= create_engine(os.getenv("DATABASE_URL"))
db =scoped_session(sessionmaker(bind=engine))

### Querys de creacion de las tablas
query_create_users = "CREATE TABLE publicacion(id SERIAL PRIMARY KEY NOT NULL, descripcion VARCHAR NOT NULL, imagen1 VARCHAR, imagen2 VARCHAR, id_user INTEGER REFERENCES usuarios)"

### Crea las tablas usando las querys
db.execute(query_create_users)

db.commit()

print("Tablas creadas")