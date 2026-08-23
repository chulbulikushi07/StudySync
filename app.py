# importing tools from Flask
from flask import Flask, render_template, request, redirect ,url_for

# this creates the actual flask application
app = Flask(__name__)

#@app.route() means that, When someone visits /, execute the home() function , thi sis also called a decorator
#URL -> Python function
#render_template() is how flask talks to html, it looks inside templates/ finds the html file and sends it to the browser

# -------------------- PUBLIC ROUTES --------------------

@app.route("/")
def home():
    return render_template("index.html")

# -------------------- ACADEMIC FEATURES --------------------

#GET, used when you're asking something
#POST, used when you're submiting data
@app.route("/assignments", methods=["GET","POST"]) #This URL can handle both displaying the page and receiving submitted data.
def assignments():
    #checks if the user input and data
    if request.method == "POST":
    
    #connection between the frontend and the backend   
        title = request.form["title"]
        subject = request.form["subject"]
        due_date = request.form["due_date"]
        priority = request.form["priority"]
        description = request.form["description"]
    #prints out the information    
        print("Title:", title)
        print("Subject", subject)
        print("Due Date",due_date)
        print("Priority",priority)
        print("Description",description)
        
        return redirect(url_for("assignments"))
        
    return render_template("assignments.html")


# -------------------- DASHBOARD --------------------

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/goals")
def goals():
    return render_template("goals.html")

@app.route("/notes")
def notes():
    return render_template("notes.html")

@app.route("/progress")
def progress():
    return render_template("progress.html")

@app.route("/timetable")
def timetable():
    return render_template("timetable.html")

# -------------------- PRODUCTIVITY --------------------

@app.route("/pomodoro")
def pomodoro():
    return render_template("pomodoro.html")

# -------------------- USER --------------------

@app.route("/profile")
def profile():
    return render_template("profile.html")


# -------------------- RUN APPLICATION --------------------

#If this Python file is being run directly, start the Flask server

if __name__ == "__main__":   
    app.run(debug = True)
       
#is useful because Flask automatically reloads when you change your code.
#It also gives you detailed error pages. 