from io import BytesIO
import os
import uuid

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, send_file, session
from werkzeug.utils import secure_filename

from auth import login_user, register_user
from db import conn, cursor
from encryption import decrypt_file, encrypt_file

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", os.getenv("SECRET_KEY", os.urandom(32).hex()))

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_file_by_id(file_id):
    cursor.execute(
        """
        SELECT filename, filepath, created_at, file_id, owner
        FROM files
        WHERE file_id=%s
        """,
        (file_id,)
    )
    return cursor.fetchone()


def get_accessible_file(file_id, username):
    cursor.execute(
        """
        SELECT filename, filepath, created_at, file_id, owner
        FROM files
        WHERE file_id=%s AND (
            owner=%s OR file_id IN (
                SELECT file_id FROM file_access WHERE username=%s
            )
        )
        """,
        (file_id, username, username)
    )
    return cursor.fetchone()


def get_owned_file(file_id, username):
    cursor.execute(
        """
        SELECT filename, filepath, created_at, file_id, owner
        FROM files
        WHERE file_id=%s AND owner=%s
        """,
        (file_id, username)
    )
    return cursor.fetchone()


def send_decrypted_file(filepath, filename):
    with open(filepath, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data = decrypt_file(encrypted_data)
    return send_file(
        BytesIO(decrypted_data),
        as_attachment=True,
        download_name=filename
    )


@app.route('/')
def home():
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        success = register_user(username, password)

        if success:
            flash("Registered successfully! Please login.")
            return redirect('/login')

        flash("User already exists!")
        return redirect('/register')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = login_user(username, password)

        if user:
            session['user'] = username
            if 'pending_file' in session:
                file_id = session.pop('pending_file')
                return redirect(f'/secure-share/{file_id}')
            return redirect('/upload')

        flash("Invalid credentials!")
        return redirect('/login')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out!")
    return redirect('/login')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    user_folder = os.path.join(UPLOAD_FOLDER, user)
    os.makedirs(user_folder, exist_ok=True)

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file selected!")
            return redirect('/upload')

        file = request.files['file']
        if file.filename == '':
            flash("No file chosen!")
            return redirect('/upload')

        filename = secure_filename(file.filename)
        if not filename:
            flash("Invalid file name!")
            return redirect('/upload')

        data = file.read()
        encrypted_data = encrypt_file(data)

        file_id = str(uuid.uuid4())
        filepath = os.path.join(user_folder, f"{file_id}_{filename}")

        with open(filepath, 'wb') as f:
            f.write(encrypted_data)

        cursor.execute(
            "INSERT INTO files (filename, owner, filepath, file_id) VALUES (%s, %s, %s, %s)",
            (filename, user, filepath, file_id)
        )
        conn.commit()

        flash("File uploaded successfully!")
        return redirect('/upload')

    cursor.execute(
        """
        SELECT filename, filepath, created_at, file_id, owner
        FROM files
        WHERE owner=%s
        OR file_id IN (
            SELECT file_id FROM file_access WHERE username=%s
        )
        """,
        (user, user)
    )

    results = cursor.fetchall()
    files = []

    for filename, filepath, created_at, file_id, owner in results:
        if os.path.exists(filepath):
            files.append({
                "original": filename,
                "size": round(os.path.getsize(filepath) / 1024, 2),
                "time": created_at,
                "file_id": file_id,
                "owner": "You" if owner == user else "Shared",
            })

    return render_template('upload.html', files=files)


@app.route('/download/<file_id>')
def download(file_id):
    if 'user' not in session:
        return redirect('/login')

    result = get_accessible_file(file_id, session['user'])
    if not result:
        return "Access denied!"

    filename, filepath, _, _, _ = result
    return send_decrypted_file(filepath, filename)


@app.route('/download_encrypted/<file_id>')
def download_encrypted(file_id):
    if 'user' not in session:
        return redirect('/login')

    result = get_accessible_file(file_id, session['user'])
    if not result:
        return "Access denied!"

    filename, filepath, _, _, _ = result
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"{filename}.encrypted"
    )


@app.route('/share/<file_id>')
def share(file_id):
    return redirect(f'/secure-share/{file_id}')


@app.route('/delete/<file_id>')
def delete(file_id):
    if 'user' not in session:
        return redirect('/login')

    result = get_owned_file(file_id, session['user'])
    if not result:
        flash("File not found or access denied!")
        return redirect('/upload')

    _, filepath, _, _, _ = result

    if os.path.exists(filepath):
        os.remove(filepath)

    cursor.execute("DELETE FROM file_access WHERE file_id=%s", (file_id,))
    cursor.execute("DELETE FROM files WHERE file_id=%s", (file_id,))
    conn.commit()

    flash("File deleted successfully!")
    return redirect('/upload')


@app.route('/secure-share/<file_id>')
def secure_share(file_id):
    if 'user' not in session:
        session['pending_file'] = file_id
        return redirect('/login')

    current_user = session['user']
    result = get_file_by_id(file_id)

    if not result:
        return "Invalid link!"

    filename, filepath, _, _, owner = result

    if owner != current_user:
        cursor.execute(
            "SELECT * FROM file_access WHERE file_id=%s AND username=%s",
            (file_id, current_user)
        )

        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO file_access (file_id, username) VALUES (%s, %s)",
                (file_id, current_user)
            )
            conn.commit()

    return send_decrypted_file(filepath, filename)


@app.route('/share_user', methods=['POST'])
def share_user():
    if 'user' not in session:
        return redirect('/login')

    file_id = request.form['file_id']
    target_user = request.form['username']
    current_user = session['user']

    if not get_owned_file(file_id, current_user):
        flash("You can only share files you own!")
        return redirect('/upload')

    cursor.execute("SELECT * FROM users WHERE username=%s", (target_user,))
    if not cursor.fetchone():
        flash("User does not exist!")
        return redirect('/upload')

    cursor.execute(
        "SELECT * FROM file_access WHERE file_id=%s AND username=%s",
        (file_id, target_user)
    )

    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO file_access (file_id, username) VALUES (%s, %s)",
            (file_id, target_user)
        )
        conn.commit()

    flash(f"File shared with {target_user}!")
    return redirect('/upload')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
