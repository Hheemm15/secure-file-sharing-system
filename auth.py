from db import conn, cursor
import hashlib

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Register user
def register_user(username, password):
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()   # 🔥 VERY IMPORTANT
        print("DB ERROR:", e)
        return False


# Login user
def login_user(username, password):
    try:
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        return cursor.fetchone()
    except Exception as e:
        conn.rollback()   # 🔥 VERY IMPORTANT
        print("DB ERROR:", e)
        return None