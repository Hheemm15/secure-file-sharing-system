import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

_connection = None
_cursor = None


def _get_database_settings():
    password = os.getenv("DB_PASSWORD")
    if not password:
        raise RuntimeError("DB_PASSWORD is missing. Add it to your .env file.")

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "secure_files"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": password,
    }


def get_connection():
    global _connection, _cursor

    if _connection is None:
        _connection = psycopg2.connect(**_get_database_settings())
        _cursor = _connection.cursor()

    return _connection


def get_cursor():
    if _cursor is None:
        get_connection()

    return _cursor


class ConnectionProxy:
    def __getattr__(self, name):
        return getattr(get_connection(), name)


class CursorProxy:
    def __getattr__(self, name):
        return getattr(get_cursor(), name)


conn = ConnectionProxy()
cursor = CursorProxy()
