from flask import Flask, request, redirect, session, render_template_string
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ASIF_HOSTING_SECRET_KEY_CHANGE_THIS"

DB = "users.db"


# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ================= COMMON STYLE =================

STYLE = """
<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #101827;
    color: white;
}

header {
    padding: 25px;
    text-align: center;
    background: #17243a;
}

header h1 {
    color: #38e8a5;
    margin: 0 0 8px;
}

.container {
    max-width: 850px;
    margin: 35px auto;
    padding: 15px;
}

.card {
    background: #1d2b42;
    padding: 25px;
    border-radius: 15px;
    margin-bottom: 18px;
    box-shadow: 0 8px 25px rgba(0,0,0,.2);
}

input {
    width: 100%;
    padding: 13px;
    margin: 8px 0 15px;
    border: none;
    border-radius: 8px;
    background: #101827;
    color: white;
    outline: none;
}

button {
    background: #38e8a5;
    color: #101827;
    border: none;
    padding: 12px 22px;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: .9;
}

a {
    color: #38e8a5;
    text-decoration: none;
}

.error {
    color: #ff6b6b;
    margin-bottom: 12px;
}

.success {
    color: #38e8a5;
    margin-bottom: 12px;
}

.status {
    color: #38e8a5;
}

footer {
    text-align: center;
    padding: 25px;
    color: #aaa;
}
</style>
"""


# ================= LOGIN =================

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Login - ASIF BOT HOSTING</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
""" + STYLE + """
</head>

<body>

<header>
<h1>ASIF BOT HOSTING</h1>
<p>Login to your account</p>
</header>

<div class="container">

<div class="card">

<h2>🔐 Login</h2>

{% if error %}
<p class="error">{{ error }}</p>
{% endif %}

<form method="POST">

<label>Username</label>
<input type="text" name="username" placeholder="Enter username" required>

<label>Password</label>
<input type="password" name="password" placeholder="Enter password" required>

<button type="submit">Login</button>

</form>

<p>
Don't have an account?
<a href="/register">Create Account</a>
</p>

</div>

</div>

<footer>© 2026 ASIF BOT HOSTING</footer>

</body>
</html>
"""


# ================= REGISTER =================

REGISTER_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Register - ASIF BOT HOSTING</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
""" + STYLE + """
</head>

<body>

<header>
<h1>ASIF BOT HOSTING</h1>
<p>Create your hosting account</p>
</header>

<div class="container">

<div class="card">

<h2>📝 Registration</h2>

{% if error %}
<p class="error">{{ error }}</p>
{% endif %}

<form method="POST">

<label>Username</label>
<input type="text" name="username" placeholder="Choose username" required>

<label>Password</label>
<input type="password" name="password" placeholder="Choose password" required>

<label>Confirm Password</label>
<input type="password" name="confirm" placeholder="Confirm password" required>

<button type="submit">Create Account</button>

</form>

<p>
Already have an account?
<a href="/login">Login</a>
</p>

</div>

</div>

<footer>© 2026 ASIF BOT HOSTING</footer>

</body>
</html>
"""


# ================= DASHBOARD =================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Dashboard - ASIF BOT HOSTING</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
""" + STYLE + """
</head>

<body>

<header>
<h1>ASIF BOT HOSTING</h1>
<p>Powerful Telegram Bot Hosting Platform</p>
</header>

<div class="container">

<div class="card">

<h2>👋 Welcome, {{ username }}!</h2>

<p>Manage your Telegram bots from one dashboard.</p>

<button onclick="location.href='#upload'">
🚀 Get Started
</button>

<a href="/logout">
<button style="margin-left:8px;">
Logout
</button>
</a>

</div>


<div class="card">

<h3>🤖 My Bots</h3>

<p class="status">
No bots uploaded yet
</p>

</div>


<div class="card" id="upload">

<h3>📤 Bot Upload</h3>

<p>Bot upload system will be added in the next step.</p>

<button disabled>
Upload Bot
</button>

</div>


<div class="card">

<h3>⚡ Hosting Features</h3>

<p>✓ Easy Bot Management</p>
<p>✓ Bot Console</p>
<p>✓ File Management</p>
<p>✓ Backup System</p>
<p>✓ 24/7 Hosting</p>

</div>

</div>

<footer>© 2026 ASIF BOT HOSTING</footer>

</body>
</html>
"""


# ================= ROUTES =================

@app.route("/")
def home():

    if "username" not in session:
        return redirect("/login")

    return render_template_string(
        DASHBOARD_HTML,
        username=session["username"]
    )


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]
        confirm = request.form["confirm"]

        if not username or not password:
            return render_template_string(
                REGISTER_HTML,
                error="Username and password required."
            )

        if password != confirm:
            return render_template_string(
                REGISTER_HTML,
                error="Passwords do not match."
            )

        if len(password) < 6:
            return render_template_string(
                REGISTER_HTML,
                error="Password must be at least 6 characters."
            )

        conn = sqlite3.connect(DB)

        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return render_template_string(
                REGISTER_HTML,
                error="Username already exists."
            )

        conn.close()

        return redirect("/login")

    return render_template_string(
        REGISTER_HTML,
        error=None
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        conn = sqlite3.connect(DB)
        user = conn.execute(
            "SELECT username, password FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user[1], password):

            session["username"] = user[0]

            return redirect("/")

        return render_template_string(
            LOGIN_HTML,
            error="Invalid username or password."
        )

    return render_template_string(
        LOGIN_HTML,
        error=None
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# ================= RUN =================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
)
