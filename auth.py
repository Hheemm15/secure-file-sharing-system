from db import conn, cursor
import hashlib

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Register user
def register_user(username, password):
    hashed = hash_password(password)

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed)
        )
        conn.commit()
        return True
    except:
        return False


# Login user
def login_user(username, password):
    hashed = hash_password(password)

    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, hashed)
    )

    return cursor.fetchone()