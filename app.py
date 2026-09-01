from flask import Flask, render_template

import storage

app = Flask(__name__)


@app.route("/")
def dashboard():
    posts = storage.get_recent_posts(hours=24)
    return render_template("dashboard.html", posts=posts)


if __name__ == "__main__":
    storage.init_db()
    app.run(debug=True, port=5001)
