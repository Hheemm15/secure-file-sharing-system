from flask import Flask, render_template, request, redirect, send_file, session, flash
from auth import register_user, login_user
from encryption import encrypt_file, decrypt_file
from db import conn, cursor
import os
import time
import uuid

app = Flask(__name__)
app.secret_key = 'k2oqzkfP8rFriQmJbb079iQ9mApYPJApuyhmkAR4PAk='

UPLOAD_FOLDER = 'uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ================= HOME =================
@app.route('/')
def home():
    return redirect('/login')


# ================= REGISTER =================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        success = register_user(username, password)

        if success:
            flash("Registered successfully! Please login.")
            return redirect('/login')
        else:
            flash("User already exists!")
            return redirect('/register')

    return render_template('register.html')


# ================= LOGIN =================
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
        else:
            flash("Invalid credentials!")
            return redirect('/login')

    return render_template('login.html')


# ================= LOGOUT =================
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

    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    # ================= UPLOAD =================
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file selected!")
            return redirect('/upload')

        file = request.files['file']

        if file.filename == '':
            flash("No file chosen!")
            return redirect('/upload')

        data = file.read()

        try:
            decrypt_file(data)
            encrypted_data = data
        except:
            encrypted_data = encrypt_file(data)

        file_id = str(uuid.uuid4())
        filename = file.filename

        filepath = os.path.join(user_folder, file_id + "_" + filename)

        with open(filepath, 'wb') as f:
            f.write(encrypted_data)

        cursor.execute(
            "INSERT INTO files (filename, owner, filepath, file_id) VALUES (%s, %s, %s, %s)",
            (filename, user, filepath, file_id)
        )
        conn.commit()

        flash("File uploaded successfully!")
        return redirect('/upload')

    # ================= FILE LIST =================
    cursor.execute("""
        SELECT filename, filepath, created_at, file_id, owner
        FROM files
        WHERE owner=%s
        OR file_id IN (
            SELECT file_id FROM file_access WHERE username=%s
        )
    """, (user, user))

    results = cursor.fetchall()

    files = []
    for row in results:
        filename, filepath, created_at, file_id, owner = row

        if os.path.exists(filepath):
            files.append({
                "name": os.path.basename(filepath),
                "original": filename,
                "size": round(os.path.getsize(filepath)/1024, 2),
                "time": created_at,
                "file_id": file_id,
                "owner": "You" if owner == user else "Shared"
            })

    return render_template('upload.html', files=files)


# ================= DOWNLOAD =================
@app.route('/download/<path:filename>')
def download(filename):
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    filepath = os.path.join(UPLOAD_FOLDER, user, filename)

    # check access
    cursor.execute("""
        SELECT * FROM files 
        WHERE filepath=%s AND (
            owner=%s OR file_id IN (
                SELECT file_id FROM file_access WHERE username=%s
            )
        )
    """, (filepath, user, user))

    if not cursor.fetchone():
        return "Access denied!"

    with open(filepath, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data = decrypt_file(encrypted_data)

    temp_path = "temp_" + filename

    with open(temp_path, 'wb') as f:
        f.write(decrypted_data)

    return send_file(temp_path, as_attachment=True)


# ================= DOWNLOAD ENCRYPTED =================
@app.route('/download_encrypted/<path:filename>')
def download_encrypted(filename):
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    filepath = os.path.join(UPLOAD_FOLDER, user, filename)

    return send_file(filepath, as_attachment=True)


# ================= SHARE =================
@app.route('/share/<file_id>')
def share(file_id):
    cursor.execute(
        "SELECT filename, filepath FROM files WHERE file_id=%s",
        (file_id,)
    )
    result = cursor.fetchone()

    if not result:
        return "Invalid or expired link!"

    filename, filepath = result

    with open(filepath, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data = decrypt_file(encrypted_data)

    temp_path = "shared_" + filename

    with open(temp_path, 'wb') as f:
        f.write(decrypted_data)

    return send_file(temp_path, as_attachment=True)


# ================= DELETE =================
@app.route('/delete/<path:filename>')
def delete(filename):
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    filepath = os.path.join(UPLOAD_FOLDER, user, filename)

    if os.path.exists(filepath):
        os.remove(filepath)

        cursor.execute("DELETE FROM files WHERE filepath=%s", (filepath,))
        conn.commit()

        flash("File deleted successfully!")

    return redirect('/upload')

# ================= SECURE SHARE =================
@app.route('/secure-share/<file_id>')
def secure_share(file_id):
    if 'user' not in session:
        session['pending_file'] = file_id
        return redirect('/login')

    current_user = session['user']

    # Check if file exists
    cursor.execute(
        "SELECT filename, filepath FROM files WHERE file_id=%s",
        (file_id,)
    )
    result = cursor.fetchone()

    if not result:
        return "Invalid link!"

    filename, filepath = result

    #  GIVE ACCESS (instead of copying)
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

    # Download file
    with open(filepath, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data = decrypt_file(encrypted_data)

    temp_path = "shared_" + filename

    with open(temp_path, 'wb') as f:
        f.write(decrypted_data)

    return send_file(temp_path, as_attachment=True)

# ================= SHARE WITH USER =================
@app.route('/share_user', methods=['POST'])
def share_user():
    if 'user' not in session:
        return redirect('/login')

    file_id = request.form['file_id']
    target_user = request.form['username']

    # check if user exists
    cursor.execute("SELECT * FROM users WHERE username=%s", (target_user,))
    if not cursor.fetchone():
        flash("User does not exist!")
        return redirect('/upload')

    # prevent duplicate access
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

# ================= RUN =================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)