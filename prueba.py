import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv

# Carga las variables de entorno que tengo en .env

xd = [1,2,3]

print(tuple(xd))
params = {'xd': xd}

print(xd)