from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import os
import uuid
import subprocess
import signal
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ASIF_HOSTING_SECRET_KEY")

DB = "users.db"
UPLOAD_FOLDER = "bot_uploads"
ALLOWED_EXTENSIONS = {"py", "zip"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bot_name TEXT NOT NULL,
            filename TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Add columns if old database does not have them
    columns = [
        row[1] for row in cur.execute("PRAGMA table_info(bots)").fetchall()
    ]

    if "pid" not in columns:
        cur.execute("ALTER TABLE bots ADD COLUMN pid INTEGER DEFAULT NULL")

    if "status" not in columns:
        cur.execute(
            "ALTER TABLE bots ADD COLUMN status TEXT DEFAULT 'Stopped'"
        )

    conn.commit()
    conn.close()


init_db()


# ================= STYLE =================

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
    max-width: 900px;
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
    padding: 11px 18px;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    margin-top: 5px;
}

button:hover {
    opacity: .9;
}

.stop {
    background: #ff6b6b;
    color: white;
}

.delete {
    background: #ff3b30;
    color: white;
}

a {
    color: #38e8a5;
    text-decoration: none;
}

.error {
    color: #ff6b6b;
}

.success {
    color: #38e8a5;
}

.bot {
    background: #101827;
    padding: 18px;
    border-radius: 10px;
    margin-top: 14px;
}

.bot-name {
    font-size: 19px;
    font-weight: bold;
    margin-bottom: 8px;
}

.small {
    color: #aaa;
    font-size: 13px;
}

.running {
    color: #38e8a5;
    font-weight: bold;
}

.stopped {
    color: #ff6b6b;
    font-weight: bold;
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
<input
type="text"
name="username"
placeholder="Enter username"
required
>

<label>Password</label>
<input
type="password"
name="password"
placeholder="Enter password"
required
>

<button type="submit">Login</button>

</form>

<p>
Don't have an account?
<a href="/register">Create Account</a>
</p>

</div>

</div>

<footer>
© 2026 ASIF BOT HOSTING
</footer>

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

<input
type="text"
name="username"
placeholder="Choose username"
required
>

<label>Password</label>

<input
type="password"
name="password"
placeholder="Choose password"
required
>

<label>Confirm Password</label>

<input
type="password"
name="confirm"
placeholder="Confirm password"
required
>

<button type="submit">
Create Account
</button>

</form>

<p>
Already have an account?
<a href="/login">Login</a>
</p>

</div>

</div>

<footer>
© 2026 ASIF BOT HOSTING
</footer>

</body>
</html>
"""


# ================= DASHBOARD =================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>

<head>

<title>Dashboard - ASIF BOT HOSTING</title>

<meta
name="viewport"
content="width=device-width, initial-scale=1"
>

""" + STYLE + """

</head>

<body>

<header>

<h1>ASIF BOT HOSTING</h1>

<p>
Powerful Telegram Bot Hosting Platform
</p>

</header>


<div class="container">


<div class="card">

<h2>
👋 Welcome, {{ username }}!
</h2>

<p>
Manage your Telegram bots from one dashboard.
</p>

<a href="#upload">

<button>
🚀 Upload Bot
</button>

</a>

<a href="/logout">

<button style="margin-left:8px;">
Logout
</button>

</a>

</div>



<div class="card">

<h3>
🤖 My Bots
</h3>


{% if bots %}

{% for bot in bots %}

<div class="bot">

<div class="bot-name">
🤖 {{ bot[1] }}
</div>

<p class="small">
File: {{ bot[2] }}
</p>

<p class="small">
Uploaded: {{ bot[3] }}
</p>


{% if bot[5] == "Running" %}

<p class="running">
● Running
</p>

<form
method="POST"
action="/stop/{{ bot[0] }}"
style="display:inline;"
>

<button
type="submit"
class="stop"
>
⛔ Stop
</button>

</form>


{% else %}

<p class="stopped">
● Stopped
</p>

<form
method="POST"
action="/start/{{ bot[0] }}"
style="display:inline;"
>

<button type="submit">
▶️ Start
</button>

</form>

{% endif %}


<form
method="POST"
action="/delete/{{ bot[0] }}"
style="display:inline;"
onsubmit="return confirm('Delete this bot?');"
>

<button
type="submit"
class="delete"
>
🗑 Delete
</button>

</form>


</div>

{% endfor %}

{% else %}

<p class="status">
No bots uploaded yet.
</p>

{% endif %}

</div>



<div class="card" id="upload">

<h3>
📤 Upload New Bot
</h3>


{% if message %}

<p class="success">
{{ message }}
</p>

{% endif %}


{% if upload_error %}

<p class="error">
{{ upload_error }}
</p>

{% endif %}


<form
method="POST"
action="/upload"
enctype="multipart/form-data"
>


<label>
Bot Name
</label>

<input
type="text"
name="bot_name"
placeholder="Example: My Telegram Bot"
required
>


<label>
Bot File
</label>

<input
type="file"
name="bot_file"
accept=".py,.zip"
required
>


<button type="submit">
📤 Upload Bot
</button>

</form>


<p class="small">
Allowed files: .py and .zip
</p>

</div>



<div class="card">

<h3>
⚡ Hosting Features
</h3>

<p>✓ User Accounts</p>
<p>✓ Bot Upload</p>
<p>✓ Start / Stop Bot</p>
<p>✓ Running / Stopped Status</p>
<p>✓ Delete Bot</p>
<p>✓ My Bots Dashboard</p>

</div>


</div>


<footer>
© 2026 ASIF BOT HOSTING
</footer>


</body>
</html>
"""


# ================= USER =================

def get_current_user():

    if "username" not in session:
        return None

    conn = sqlite3.connect(DB)

    user = conn.execute(
        """
        SELECT id, username
        FROM users
        WHERE username = ?
        """,
        (session["username"],)
    ).fetchone()

    conn.close()

    return user


# ================= BOT PROCESS =================

def get_bot(bot_id, user_id):

    conn = sqlite3.connect(DB)

    bot = conn.execute(
        """
        SELECT id, bot_name, filename, pid, status
        FROM bots
        WHERE id = ? AND user_id = ?
        """,
        (bot_id, user_id)
    ).fetchone()

    conn.close()

    return bot


def is_process_running(pid):

    if not pid:
        return False

    try:
        os.kill(pid, 0)
        return True
    except:
        return False


def update_status(bot_id, pid, status):

    conn = sqlite3.connect(DB)

    conn.execute(
        """
        UPDATE bots
        SET pid = ?, status = ?
        WHERE id = ?
        """,
        (pid, status, bot_id)
    )

    conn.commit()
    conn.close()


# ================= HOME =================

@app.route("/")
def home():

    user = get_current_user()

    if not user:
        return redirect("/login")

    conn = sqlite3.connect(DB)

    bots = conn.execute(
        """
        SELECT id,
               bot_name,
               filename,
               created_at,
               pid,
               status
        FROM bots
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user[0],)
    ).fetchall()

    conn.close()

    # Check real process status
    for bot in bots:

        if bot[4]:

            if is_process_running(bot[4]):

                if bot[5] != "Running":
                    update_status(
                        bot[0],
                        bot[4],
                        "Running"
                    )

            else:

                if bot[5] != "Stopped":
                    update_status(
                        bot[0],
                        None,
                        "Stopped"
                    )

    # Reload bots
    conn = sqlite3.connect(DB)

    bots = conn.execute(
        """
        SELECT id,
               bot_name,
               filename,
               created_at,
               pid,
               status
        FROM bots
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user[0],)
    ).fetchall()

    conn.close()

    return render_template_string(
        DASHBOARD_HTML,
        username=user[1],
        bots=bots,
        message=None,
        upload_error=None
    )


# ================= REGISTER =================

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
                """
                INSERT INTO users
                (username, password)
                VALUES (?, ?)
                """,
                (
                    username,
                    generate_password_hash(password)
                )
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


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        conn = sqlite3.connect(DB)

        user = conn.execute(
            """
            SELECT username, password
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user[1],
            password
        ):

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


# ================= UPLOAD =================

@app.route("/upload", methods=["POST"])
def upload_bot():

    user = get_current_user()

    if not user:
        return redirect("/login")

    bot_name = request.form.get(
        "bot_name",
        ""
    ).strip()

    bot_file = request.files.get(
        "bot_file"
    )

    if not bot_name:
        return redirect("/")

    if not bot_file or not bot_file.filename:
        return redirect("/")

    original_name = secure_filename(
        bot_file.filename
    )

    extension = (
        original_name.rsplit(".", 1)[-1].lower()
        if "." in original_name
        else ""
    )

    if extension not in ALLOWED_EXTENSIONS:

        return render_template_string(
            DASHBOARD_HTML,
            username=user[1],
            bots=[],
            message=None,
            upload_error="Only .py and .zip files are allowed."
        )

    unique_name = (
        str(uuid.uuid4())
        + "_"
        + original_name
    )

    user_folder = os.path.join(
        UPLOAD_FOLDER,
        str(user[0])
    )

    os.makedirs(
        user_folder,
        exist_ok=True
    )

    file_path = os.path.join(
        user_folder,
        unique_name
    )

    bot_file.save(file_path)

    conn = sqlite3.connect(DB)

    conn.execute(
        """
        INSERT INTO bots
        (user_id, bot_name, filename, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            user[0],
            bot_name,
            original_name,
            "Stopped"
        )
    )

    conn.commit()
    conn.close()

    return redirect("/")


# ================= START BOT =================

@app.route("/start/<int:bot_id>", methods=["POST"])
def start_bot(bot_id):

    user = get_current_user()

    if not user:
        return redirect("/login")

    bot = get_bot(
        bot_id,
        user[0]
    )

    if not bot:
        return redirect("/")

    # Already running
    if bot[3] and is_process_running(bot[3]):

        update_status(
            bot_id,
            bot[3],
            "Running"
        )

        return redirect("/")

    user_folder = os.path.join(
        UPLOAD_FOLDER,
        str(user[0])
    )

    # Find uploaded file
    files = os.listdir(user_folder)

    target_file = None

    for filename in files:

        if filename.endswith(
            "_" + secure_filename(bot[2])
        ):

            target_file = os.path.join(
                user_folder,
                filename
            )

            break

    if not target_file:
        return redirect("/")

    # Only Python files can directly run
    if not target_file.endswith(".py"):

        return redirect("/")

    try:

        process = subprocess.Popen(
            ["python", target_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        update_status(
            bot_id,
            process.pid,
            "Running"
        )

    except Exception:

        update_status(
            bot_id,
            None,
            "Stopped"
        )

    return redirect("/")


# ================= STOP BOT =================

@app.route("/stop/<int:bot_id>", methods=["POST"])
def stop_bot(bot_id):

    user = get_current_user()

    if not user:
        return redirect("/login")

    bot = get_bot(
        bot_id,
        user[0]
    )

    if not bot:
        return redirect("/")

    pid = bot[3]

    if pid:

        try:

            os.kill(
                pid,
                signal.SIGTERM
            )

        except:

            pass

    update_status(
        bot_id,
        None,
        "Stopped"
    )

    return redirect("/")


# ================= DELETE BOT =================

@app.route("/delete/<int:bot_id>", methods=["POST"])
def delete_bot(bot_id):

    user = get_current_user()

    if not user:
        return redirect("/login")

    bot = get_bot(
        bot_id,
        user[0]
    )

    if not bot:
        return redirect("/")

    # Stop first
    pid = bot[3]

    if pid:

        try:

            os.kill(
                pid,
                signal.SIGTERM
            )

        except:

            pass

    user_folder = os.path.join(
        UPLOAD_FOLDER,
        str(user[0])
    )

    # Delete matching file
    if os.path.exists(user_folder):

        for filename in os.listdir(
            user_folder
        ):

            if filename.endswith(
                "_" + secure_filename(bot[2])
            ):

                try:

                    os.remove(
                        os.path.join(
                            user_folder,
                            filename
                        )
                    )

                except:

                    pass

    conn = sqlite3.connect(DB)

    conn.execute(
        """
        DELETE FROM bots
        WHERE id = ? AND user_id = ?
        """,
        (
            bot_id,
            user[0]
        )
    )

    conn.commit()
    conn.close()

    return redirect("/")


# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# ================= RUN =================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
