import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

db_name = os.getenv('NAME')
db_password = os.getenv('PASSWORD')
db_host = os.getenv('HOST')
db_drivername = os.getenv('DRIVERNAME')
db_username = os.getenv('USERNAME')

url = URL.create(
    drivername=db_drivername,
    host=db_host,
    password=db_password,
    username=db_username,
    database=db_name
)

engine = create_engine(url=url, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()