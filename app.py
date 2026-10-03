
from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ASIF BOT HOSTING</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
    margin: 0;
    font-family: Arial;
    background: #101827;
    color: white;
}
header {
    padding: 25px;
    text-align: center;
    background: #17243a;
}
header h1 { color: #38e8a5; }
.container {
    max-width: 850px;
    margin: 35px auto;
    padding: 15px;
}
.card {
    background: #1d2b42;
    padding: 22px;
    border-radius: 15px;
    margin-bottom: 18px;
}
button {
    background: #38e8a5;
    color: #101827;
    border: none;
    padding: 12px 22px;
    border-radius: 8px;
    font-weight: bold;
}
.status { color: #38e8a5; }
footer {
    text-align: center;
    padding: 25px;
    color: #aaa;
}
</style>
</head>
<body>
<header>
<h1>ASIF BOT HOSTING</h1>
<p>Powerful Telegram Bot Hosting Platform</p>
</header>

<div class="container">
<div class="card">
<h2>Welcome to ASIF Hosting</h2>
<p>Manage your Telegram bots from one dashboard.</p>
<button>Get Started</button>
</div>

<div class="card">
<h3>My Bots</h3>
<p class="status">No bots uploaded yet</p>
</div>

<div class="card">
<h3>Hosting Features</h3>
<p>✓ Easy Bot Management</p>
<p>✓ Bot Console</p>
<p>✓ File Management</p>
<p>✓ Backup System</p>
</div>
</div>

<footer>© 2026 ASIF BOT HOSTING</footer>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
