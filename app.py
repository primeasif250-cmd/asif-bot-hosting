from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import os
import uuid
import subprocess
import signal
import zipfile
import shutil
import sys
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ASIF_HOSTING_SECRET_KEY")

DB = "users.db"
UPLOAD_FOLDER = "bot_uploads"

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
            bot_folder TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pid INTEGER DEFAULT NULL,
            status TEXT DEFAULT 'Stopped',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    columns = [
        row[1]
        for row in cur.execute(
            "PRAGMA table_info(bots)"
        ).fetchall()
    ]

    if "bot_folder" not in columns:
        cur.execute(
            "ALTER TABLE bots ADD COLUMN bot_folder TEXT DEFAULT ''"
        )

    if "pid" not in columns:
        cur.execute(
            "ALTER TABLE bots ADD COLUMN pid INTEGER DEFAULT NULL"
        )

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
    margin: 30px auto;
    padding: 15px;
}

.card {
    background: #1d2b42;
    padding: 24px;
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
}

button {
    background: #38e8a5;
    color: #101827;
    border: none;
    padding: 11px 18px;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    margin: 4px;
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

.running {
    color: #38e8a5;
    font-weight: bold;
}

.stopped {
    color: #ff6b6b;
    font-weight: bold;
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
}

.small {
    color: #aaa;
    font-size: 13px;
}

footer {
    text-align: center;
    padding: 25px;
    color: #aaa;
}
</style>
"""


# ================= LOGIN PAGE =================

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

<button type="submit">
Login
</button>

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


# ================= REGISTER PAGE =================

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
<button>
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
Main file: {{ bot[2] }}
</p>

<p class="small">
Uploaded: {{ bot[3] }}
</p>


{% if bot[6] == "Running" %}

<p class="running">
🟢 Running
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
🔴 Stopped
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
onsubmit="return confirm('Delete this bot permanently?');"
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

<p>
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
Bot File / ZIP
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
Upload .py or .zip
</p>

<p class="small">
ZIP should contain bot.py and requirements.txt
</p>

</div>


<div class="card">

<h3>
⚡ Hosting Features
</h3>

<p>✓ User Accounts</p>
<p>✓ Bot Upload</p>
<p>✓ requirements.txt Support</p>
<p>✓ ZIP Bot Support</p>
<p>✓ Start / Stop</p>
<p>✓ Running / Stopped Status</p>
<p>✓ Delete Bot</p>

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


# ================= BOT =================

def get_bot(bot_id, user_id):

    conn = sqlite3.connect(DB)

    bot = conn.execute(
        """
        SELECT
            id,
            bot_name,
            filename,
            bot_folder,
            created_at,
            pid,
            status
        FROM bots
        WHERE id = ? AND user_id = ?
        """,
        (bot_id, user_id)
    ).fetchone()

    conn.close()

    return bot


def process_running(pid):

    if not pid:
        return False

    try:
        os.kill(pid, 0)
        return True
    except:
        return False


def update_bot_status(bot_id, pid, status):

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
        SELECT
            id,
            bot_name,
            filename,
            created_at,
            bot_folder,
            pid,
            status
        FROM bots
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user[0],)
    ).fetchall()

    conn.close()

    # Refresh status
    for bot in bots:

        if bot[5]:

            if process_running(bot[5]):

                if bot[6] != "Running":
                    update_bot_status(
                        bot[0],
                        bot[5],
                        "Running"
                    )

            else:

                update_bot_status(
                    bot[0],
                    None,
                    "Stopped"
                )

    conn = sqlite3.connect(DB)

    bots = conn.execute(
        """
        SELECT
            id,
            bot_name,
            filename,
            created_at,
            bot_folder,
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

    if extension not in {"py", "zip"}:

        return redirect("/")

    bot_id_folder = str(uuid.uuid4())

    user_folder = os.path.join(
        UPLOAD_FOLDER,
        str(user[0])
    )

    bot_folder = os.path.join(
        user_folder,
        bot_id_folder
    )

    os.makedirs(
        bot_folder,
        exist_ok=True
    )


    # ================= PY FILE =================

    if extension == "py":

        file_path = os.path.join(
            bot_folder,
            original_name
        )

        bot_file.save(file_path)

        main_file = original_name


    # ================= ZIP FILE =================

    else:

        zip_path = os.path.join(
            bot_folder,
            "upload.zip"
        )

        bot_file.save(zip_path)

        try:

            with zipfile.ZipFile(
                zip_path,
                "r"
            ) as zip_ref:

                zip_ref.extractall(
                    bot_folder
                )

            os.remove(zip_path)

        except Exception:

            shutil.rmtree(
                bot_folder,
                ignore_errors=True
            )

            return redirect("/")

        # Find bot.py
        main_file = None

        for root, dirs, files in os.walk(
            bot_folder
        ):

            if "bot.py" in files:

                main_file = os.path.relpath(
                    os.path.join(
                        root,
                        "bot.py"
                    ),
                    bot_folder
                )

                break

        if not main_file:

            shutil.rmtree(
                bot_folder,
                ignore_errors=True
            )

            return redirect("/")


    # ================= DATABASE =================

    conn = sqlite3.connect(DB)

    conn.execute(
        """
        INSERT INTO bots
        (
            user_id,
            bot_name,
            filename,
            bot_folder,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user[0],
            bot_name,
            main_file,
            bot_id_folder,
            "Stopped"
        )
    )

    conn.commit()
    conn.close()

    return redirect("/")


# ================= INSTALL REQUIREMENTS =================

def install_requirements(bot_folder):

    requirements_file = os.path.join(
        bot_folder,
        "requirements.txt"
    )

    if not os.path.exists(
        requirements_file
    ):
        return True

    try:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                requirements_file,
                "--user"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )

        return result.returncode == 0

    except:

        return False


# ================= START =================

@app.route(
    "/start/<int:bot_id>",
    methods=["POST"]
)
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

    if bot[5] and process_running(
        bot[5]
    ):

        update_bot_status(
            bot_id,
            bot[5],
            "Running"
        )

        return redirect("/")


    bot_folder = os.path.join(
        UPLOAD_FOLDER,
        str(user[0]),
        bot[3]
    )

    if not os.path.exists(
        bot_folder
    ):
        return redirect("/")


    main_file = os.path.join(
        bot_folder,
        bot[2]
    )

    if not os.path.exists(
        main_file
    ):
        return redirect("/")


    # Install requirements
    requirements_ok = install_requirements(
        bot_folder
    )

    if not requirements_ok:

        update_bot_status(
            bot_id,
            None,
            "Stopped"
        )

        return redirect("/")


    try:

        process = subprocess.Popen(
            [
                sys.executable,
                main_file
            ],
            cwd=bot_folder,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        update_bot_status(
            bot_id,
            process.pid,
            "Running"
        )

    except:

        update_bot_status(
            bot_id,
            None,
            "Stopped"
        )

    return redirect("/")


# ================= STOP =================

@app.route(
    "/stop/<int:bot_id>",
    methods=["POST"]
)
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

    pid = bot[5]

    if pid:

        try:

            os.kill(
                pid,
                signal.SIGTERM
            )

        except:

            pass

    update_bot_status(
        bot_id,
        None,
        "Stopped"
    )

    return redirect("/")


# ================= DELETE =================

@app.route(
    "/delete/<int:bot_id>",
    methods=["POST"]
)
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

    # Stop process
    if bot[5]:

        try:

            os.kill(
                bot[5],
                signal.SIGTERM
            )

        except:

            pass


    # Delete files
    bot_folder = os.path.join(
        UPLOAD_FOLDER,
        str(user[0]),
        bot[3]
    )

    if os.path.exists(
        bot_folder
    ):

        shutil.rmtree(
            bot_folder,
            ignore_errors=True
        )


    # Delete database record
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
