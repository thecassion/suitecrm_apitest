import os

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    #DB_URL
    db_url: str = Field(..., env='DATABASE_URL')
    db_host: str = Field(..., env='MYSQL_HOST')
    db_user: str = Field(..., env='MYSQL_USER')
    db_password: str = Field(..., env='MYSQL_PASSWORD')
    db_database: str = Field(..., env='MYSQL_DATABASE')
    db_port: int = Field(..., env='MYSQL_PORT')

settings = Settings()