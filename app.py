from flask import Flask, render_template, request, redirect, send_file, session, flash
from auth import register_user, login_user
from encryption import encrypt_file, decrypt_file
import os

app = Flask(__name__)
app.secret_key = 'supersecret123'

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

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file selected!")
            return redirect('/upload')

        file = request.files['file']

        if file.filename == '':
            flash("No file chosen!")
            return redirect('/upload')

        data = file.read()
        encrypted_data = encrypt_file(data)

        filepath = os.path.join('uploads', file.filename)

        with open(filepath, 'wb') as f:
            f.write(encrypted_data)

        flash("File uploaded successfully!")
        return redirect('/upload')

    # ✅ SHOW FILE LIST
    files = os.listdir('uploads')
    return render_template('upload.html', files=files)


# ================= DOWNLOAD =================
@app.route('/download/<path:filename>')
def download(filename):
    if 'user' not in session:
        return redirect('/login')

    filepath = os.path.join('uploads', filename)

    if not os.path.exists(filepath):
        return "File not found!"

    with open(filepath, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data = decrypt_file(encrypted_data)

    temp_path = "temp_" + filename

    with open(temp_path, 'wb') as f:
        f.write(decrypted_data)

    return send_file(temp_path, as_attachment=True)


# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)