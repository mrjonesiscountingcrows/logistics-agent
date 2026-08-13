import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_PATH", "logistics.db")
engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    return Session(engine)
