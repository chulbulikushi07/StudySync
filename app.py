# importing tools from Flask
from flask import Flask, render_template, request, redirect ,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# this creates the actual flask application
app = Flask(__name__)

# uses a SQLite database called studysync.db
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///studysync.db"
#Disables modification tracking,it consumes additional resources and can generate unnecessary warnings.
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#connects SQLAlchemy to Flask,creates our database object
db = SQLAlchemy(app)

class Assignment(db.Model):
    #nullable = False means the database cant accept an empty/null value.
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(150), nullable= False)
    subject = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)    

#@app.route() means that, When someone visits /, execute the home() function , this is also called a decorator
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
        due_date = datetime.strptime(request.form["due_date"], "%Y-%m-%d").date()        
        priority = request.form["priority"]
        description = request.form["description"]
    #prints out the information    
        new_assignment = Assignment(
            title=title,
            subject=subject,
            due_date=due_date,
            priority=priority,
            description=description
        )
        db.session.add(new_assignment)
        db.session.commit() 
               
        return redirect(url_for("assignments"))
        
    assignments = Assignment.query.all()
        
    return render_template(
        "assignments.html",
        assignments=assignments
    )



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
    with app.app_context():
        db.create_all()  
    app.run(debug = True)
       
#is useful because Flask automatically reloads when you change your code.
#It also gives you detailed error pages. 