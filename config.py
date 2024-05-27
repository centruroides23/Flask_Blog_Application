import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32)
    SQLALCHEMY_DATABASE_URI = "postgresql://default:************@ep-frosty-cherry-a5px8p3y.us-east-2.aws.neon.tech:5432/verceldb?sslmode=require"
