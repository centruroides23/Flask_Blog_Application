import os
basedir = os.path.abspath(os.path.dirname(__file__))
db_url = os.environ.get("POSTGRES_URL")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32)
    SQLALCHEMY_DATABASE_URI = db_url.replace("postgres://", "postgresql://")
