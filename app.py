from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/assignments")
def assignments():
    return render_template("assignments.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/goals")
def goals():
    return render_template("goals.html")

@app.route("/notes")
def notes():
    return render_template("notes.html")

@app.route("/pomodoro")
def pomodoro():
    return render_template("pomodoro.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/progress")
def progress():
    return render_template("progress.html")

@app.route("/timetable")
def timetable():
    return render_template("timetable.html")

if __name__ == "__main__":
    app.run(debug = True)