from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return redirect('/login')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # For now just print (we add real auth later)
        print("Login attempt:", username, password)

        return "Login received!"

    return render_template('login.html')

# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return "Registered!"

    return render_template('register.html')


if __name__ == '__main__':
    app.run(debug=True)
    
from auth import register_user, login_user

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