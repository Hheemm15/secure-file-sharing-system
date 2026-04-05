from flask import Flask, render_template, request, redirect, send_file, session, flash
from auth import register_user, login_user
from encryption import encrypt_file, decrypt_file
import os
import time

app = Flask(__name__)
app.secret_key = 'supersecret123'

UPLOAD_FOLDER = 'uploads'

# Ensure uploads folder exists
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


# ================= UPLOAD =================
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    user_folder = os.path.join(UPLOAD_FOLDER, user)

    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file selected!")
            return redirect('/upload')

        file = request.files['file']

        if file.filename == '':
            flash("No file chosen!")
            return redirect('/upload')

        filepath = os.path.join(user_folder, file.filename)

        data = file.read()

        # Detect encrypted file
        try:
            decrypt_file(data)
            encrypted_data = data
            flash("Encrypted file uploaded!")
        except:
            encrypted_data = encrypt_file(data)
            flash("File uploaded & encrypted!")

        with open(filepath, 'wb') as f:
            f.write(encrypted_data)

        return redirect('/upload')

    # ================= FILE LIST =================
    files = []

    if os.path.exists(user_folder):
        for filename in os.listdir(user_folder):
            filepath = os.path.join(user_folder, filename)

            files.append({
                "name": filename,
                "size": round(os.path.getsize(filepath)/1024, 2),
                "time": time.ctime(os.path.getmtime(filepath))
            })

    return render_template('upload.html', files=files)


# ================= DOWNLOAD (DECRYPTED) =================
@app.route('/download/<path:filename>')
def download(filename):
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    filepath = os.path.join(UPLOAD_FOLDER, user, filename)

    if not os.path.exists(filepath):
        return "File not found!"

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


# ================= DELETE =================
@app.route('/delete/<path:filename>')
def delete(filename):
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    filepath = os.path.join(UPLOAD_FOLDER, user, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        flash("File deleted successfully!")
    else:
        flash("File not found!")

    return redirect('/upload')


# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)