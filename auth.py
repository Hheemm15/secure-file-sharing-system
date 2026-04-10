import hashlib

from db import conn, cursor


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    try:
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("DB ERROR:", e)
        return False


def login_user(username, password):
    try:
        cursor.execute(
            "SELECT username, password FROM users WHERE username=%s",
            (username,)
        )
        user = cursor.fetchone()

        if not user:
            return None

        stored_username, stored_password = user
        hashed_password = hash_password(password)

        if stored_password == hashed_password:
            return (stored_username,)

        # Auto-migrate any legacy plain-text password record after a valid login.
        if stored_password == password:
            cursor.execute(
                "UPDATE users SET password=%s WHERE username=%s",
                (hashed_password, stored_username)
            )
            conn.commit()
            return (stored_username,)

        return None
    except Exception as e:
        conn.rollback()
        print("DB ERROR:", e)
        return None
