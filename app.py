from flask import Flask, render_template, request, redirect, send_file
from auth import register_user, login_user
from encryption import encrypt_file, decrypt_file
import os

app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return redirect('/login')


# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        success = register_user(username, password)

        if success:
            return "Registered Successfully!"
        else:
            return "User already exists!"

    return render_template('register.html')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = login_user(username, password)

        if user:
            return "Login Successful!"
        else:
            return "Invalid Credentials!"

    return render_template('login.html')


# Upload route
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']

        if file:
            data = file.read()

            encrypted_data = encrypt_file(data)

            filepath = os.path.join('uploads', file.filename)

            with open(filepath, 'wb') as f:
                f.write(encrypted_data)

            return "File uploaded & encrypted!"

    return render_template('upload.html')


# Download route (MOVE ABOVE app.run)
@app.route('/download/<path:filename>')
def download(filename):
    print("Requested file:", filename)

    filepath = os.path.join('uploads', filename)
    print("Looking in:", filepath)

    if not os.path.exists(filepath):
        return f"File NOT FOUND: {filepath}"

    with open(filepath, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data = decrypt_file(encrypted_data)

    temp_path = "temp_" + filename

    with open(temp_path, 'wb') as f:
        f.write(decrypted_data)

    return send_file(temp_path, as_attachment=True)


# Run app (ALWAYS LAST)
if __name__ == '__main__':
    app.run(debug=True)