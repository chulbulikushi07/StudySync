"""StudySync's Flask application."""

import os
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, or_, text
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///studysync.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["CSRF_ENABLED"] = os.environ.get("CSRF_ENABLED", "true").lower() != "false"
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "0") == "1"

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    assignments = db.relationship("Assignment", backref="user", lazy=True, cascade="all, delete-orphan")
    notes = db.relationship("Note", backref="user", lazy=True, cascade="all, delete-orphan")
    goals = db.relationship("Goal", backref="user", lazy=True, cascade="all, delete-orphan")
    timetable_entries = db.relationship(
        "TimetableEntry", backref="user", lazy=True, cascade="all, delete-orphan"
    )


class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="Medium")
    description = db.Column(db.Text, nullable=False, default="")
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(100), nullable=False, default="General")
    category = db.Column(db.String(100), nullable=False, default="Lecture Notes")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    goal_type = db.Column(db.String(50), nullable=False, default="Personal")
    target_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    progress = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class TimetableEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    class_name = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    day = db.Column(db.String(12), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room = db.Column(db.String(100), nullable=True)
    instructor = db.Column(db.String(100), nullable=True)


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
PRIORITIES = ["High", "Medium", "Low"]
GOAL_TYPES = ["Daily", "Weekly", "Monthly", "Semester", "Personal"]


def get_current_user():
    """Return the logged-in user, or None when the session is anonymous."""
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def login_required(view):
    """Redirect anonymous visitors to login."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if get_current_user() is None:
            flash("Please log in to access StudySync.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped_view


def csrf_token():
    token = session.get("_csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


@app.context_processor
def inject_template_helpers():
    return {
        "current_user": get_current_user(),
        "csrf_token": csrf_token,
        "days": DAYS,
        "priorities": PRIORITIES,
        "goal_types": GOAL_TYPES,
    }


@app.before_request
def validate_csrf_and_session():
    if session.get("user_id") and get_current_user() is None:
        session.clear()
    if request.method == "POST" and app.config["CSRF_ENABLED"]:
        submitted_token = request.form.get("csrf_token", "")
        if not submitted_token or not secrets.compare_digest(submitted_token, session.get("_csrf_token", "")):
            abort(400, description="Your form session expired. Please try again.")


def form_text(field, label, maximum, required=True):
    value = request.form.get(field, "").strip()
    if required and not value:
        raise ValueError(f"{label} is required.")
    if len(value) > maximum:
        raise ValueError(f"{label} must be {maximum} characters or fewer.")
    return value


def form_date(field, label, required=True):
    value = request.form.get(field, "").strip()
    if not value and not required:
        return None
    if not value:
        raise ValueError(f"{label} is required.")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError(f"{label} must be a valid date.") from error


def form_time(field, label):
    value = request.form.get(field, "").strip()
    if not value:
        raise ValueError(f"{label} is required.")
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as error:
        raise ValueError(f"{label} must be a valid time.") from error


def assignment_from_form(assignment):
    priority = form_text("priority", "Priority", 20)
    if priority not in PRIORITIES:
        raise ValueError("Please choose a valid priority.")
    assignment.title = form_text("title", "Assignment name", 150)
    assignment.subject = form_text("subject", "Subject", 100)
    assignment.due_date = form_date("due_date", "Due date")
    assignment.priority = priority
    assignment.description = form_text("description", "Description", 5000, required=False)


def note_from_form(note):
    note.title = form_text("title", "Note title", 150)
    note.subject = form_text("subject", "Subject", 100)
    note.category = form_text("category", "Category", 100)
    note.content = form_text("content", "Note content", 10000)


def goal_from_form(goal):
    goal_type = form_text("goal_type", "Goal type", 50)
    if goal_type not in GOAL_TYPES:
        raise ValueError("Please choose a valid goal type.")
    try:
        progress = int(request.form.get("progress", "0"))
    except ValueError as error:
        raise ValueError("Progress must be a whole number.") from error
    if not 0 <= progress <= 100:
        raise ValueError("Progress must be between 0 and 100.")
    goal.title = form_text("title", "Goal name", 150)
    goal.goal_type = goal_type
    goal.target_date = form_date("target_date", "Target date", required=False)
    goal.description = form_text("description", "Description", 5000, required=False)
    goal.progress = progress
    goal.completed = progress == 100


def timetable_from_form(entry):
    day = form_text("day", "Day", 12)
    if day not in DAYS:
        raise ValueError("Please choose a valid day.")
    start_time = form_time("start_time", "Start time")
    end_time = form_time("end_time", "End time")
    if start_time >= end_time:
        raise ValueError("End time must be later than start time.")
    entry.class_name = form_text("class_name", "Class name", 150)
    entry.subject = form_text("subject", "Subject", 100)
    entry.day = day
    entry.start_time = start_time
    entry.end_time = end_time
    entry.room = form_text("room", "Room", 100, required=False) or None
    entry.instructor = form_text("instructor", "Instructor", 100, required=False) or None


def percentage(completed, total):
    return round((completed / total) * 100) if total else 0


def user_assignment_or_404(assignment_id):
    return Assignment.query.filter_by(id=assignment_id, user_id=get_current_user().id).first_or_404()


def user_note_or_404(note_id):
    return Note.query.filter_by(id=note_id, user_id=get_current_user().id).first_or_404()


def user_goal_or_404(goal_id):
    return Goal.query.filter_by(id=goal_id, user_id=get_current_user().id).first_or_404()


def user_timetable_entry_or_404(entry_id):
    return TimetableEntry.query.filter_by(id=entry_id, user_id=get_current_user().id).first_or_404()


@app.route("/")
def home():
    if get_current_user():
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if get_current_user():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        try:
            name = form_text("name", "Name", 100)
            email = form_text("email", "Email", 255).lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            if "@" not in email or email.startswith("@") or email.endswith("@"):
                raise ValueError("Please enter a valid email address.")
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters long.")
            if password != confirm_password:
                raise ValueError("Passwords do not match.")
            if User.query.filter_by(email=email).first():
                raise ValueError("An account with that email already exists.")
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session.clear()
            session["user_id"] = user.id
            flash("Welcome to StudySync! Your account is ready.", "success")
            return redirect(url_for("dashboard"))
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not email or not password or not user or not check_password_hash(user.password_hash, password):
            flash("Email or password is incorrect.", "danger")
        else:
            session.clear()
            session["user_id"] = user.id
            next_page = request.args.get("next", "")
            if (
                not next_page.startswith("/")
                or next_page.startswith("//")
                or "\\" in next_page
            ):
                next_page = url_for("dashboard")
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(next_page)
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    assignment_query = Assignment.query.filter_by(user_id=user.id)
    total_assignments = assignment_query.count()
    completed_assignments = assignment_query.filter_by(completed=True).count()
    upcoming_assignments = (
        assignment_query.filter_by(completed=False)
        .filter(Assignment.due_date >= datetime.today().date())
        .order_by(Assignment.due_date.asc()).limit(5).all()
    )
    recent_notes = Note.query.filter_by(user_id=user.id).order_by(Note.updated_at.desc()).limit(3).all()
    goals = Goal.query.filter_by(user_id=user.id).all()
    goal_progress = round(sum(goal.progress for goal in goals) / len(goals)) if goals else 0
    today_entries = TimetableEntry.query.filter_by(
        user_id=user.id, day=datetime.today().strftime("%A")
    ).order_by(TimetableEntry.start_time.asc()).all()
    return render_template(
        "dashboard.html",
        total_assignments=total_assignments,
        completed_assignments=completed_assignments,
        pending_assignments=total_assignments - completed_assignments,
        assignment_progress=percentage(completed_assignments, total_assignments),
        notes_count=Note.query.filter_by(user_id=user.id).count(),
        active_goals=sum(not goal.completed for goal in goals),
        goal_progress=goal_progress,
        upcoming_assignments=upcoming_assignments,
        recent_notes=recent_notes,
        today_entries=today_entries,
    )


@app.route("/assignments", methods=["GET", "POST"])
@login_required
def assignments():
    user = get_current_user()
    if request.method == "POST":
        assignment = Assignment(user_id=user.id)
        try:
            assignment_from_form(assignment)
            db.session.add(assignment)
            db.session.commit()
            flash("Assignment added.", "success")
        except ValueError as error:
            flash(str(error), "danger")
        return redirect(url_for("assignments"))
    query = Assignment.query.filter_by(user_id=user.id)
    search = request.args.get("q", "").strip()
    subject = request.args.get("subject", "").strip()
    status = request.args.get("status", "").strip()
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Assignment.title.ilike(term), Assignment.subject.ilike(term), Assignment.description.ilike(term)))
    if subject:
        query = query.filter_by(subject=subject)
    if status == "pending":
        query = query.filter_by(completed=False)
    elif status == "completed":
        query = query.filter_by(completed=True)
    assignment_list = query.order_by(Assignment.completed.asc(), Assignment.due_date.asc()).all()
    subjects = [row[0] for row in db.session.query(Assignment.subject).filter_by(user_id=user.id).distinct().order_by(Assignment.subject).all()]
    return render_template("assignments.html", assignments=assignment_list, subjects=subjects, search=search, selected_subject=subject, selected_status=status)


@app.post("/assignments/<int:assignment_id>/edit")
@login_required
def edit_assignment(assignment_id):
    assignment = user_assignment_or_404(assignment_id)
    try:
        assignment_from_form(assignment)
        db.session.commit()
        flash("Assignment updated.", "success")
    except ValueError as error:
        flash(str(error), "danger")
    return redirect(url_for("assignments"))


@app.post("/assignments/<int:assignment_id>/toggle")
@login_required
def toggle_assignment(assignment_id):
    assignment = user_assignment_or_404(assignment_id)
    assignment.completed = not assignment.completed
    db.session.commit()
    flash("Assignment marked complete." if assignment.completed else "Assignment reopened.", "success")
    return redirect(url_for("assignments"))


@app.post("/assignments/<int:assignment_id>/delete")
@login_required
def delete_assignment(assignment_id):
    assignment = user_assignment_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash("Assignment deleted.", "success")
    return redirect(url_for("assignments"))


@app.route("/notes", methods=["GET", "POST"])
@login_required
def notes():
    user = get_current_user()
    if request.method == "POST":
        note = Note(user_id=user.id)
        try:
            note_from_form(note)
            db.session.add(note)
            db.session.commit()
            flash("Note saved.", "success")
        except ValueError as error:
            flash(str(error), "danger")
        return redirect(url_for("notes"))
    query = Note.query.filter_by(user_id=user.id)
    search = request.args.get("q", "").strip()
    subject = request.args.get("subject", "").strip()
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Note.title.ilike(term), Note.content.ilike(term)))
    if subject:
        query = query.filter_by(subject=subject)
    note_list = query.order_by(Note.updated_at.desc()).all()
    subjects = [row[0] for row in db.session.query(Note.subject).filter_by(user_id=user.id).distinct().order_by(Note.subject).all()]
    return render_template("notes.html", notes=note_list, subjects=subjects, search=search, selected_subject=subject)


@app.post("/notes/<int:note_id>/edit")
@login_required
def edit_note(note_id):
    note = user_note_or_404(note_id)
    try:
        note_from_form(note)
        db.session.commit()
        flash("Note updated.", "success")
    except ValueError as error:
        flash(str(error), "danger")
    return redirect(url_for("notes"))


@app.post("/notes/<int:note_id>/delete")
@login_required
def delete_note(note_id):
    note = user_note_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted.", "success")
    return redirect(url_for("notes"))


@app.route("/goals", methods=["GET", "POST"])
@login_required
def goals():
    user = get_current_user()
    if request.method == "POST":
        goal = Goal(user_id=user.id)
        try:
            goal_from_form(goal)
            db.session.add(goal)
            db.session.commit()
            flash("Goal added.", "success")
        except ValueError as error:
            flash(str(error), "danger")
        return redirect(url_for("goals"))
    goal_list = Goal.query.filter_by(user_id=user.id).order_by(Goal.completed.asc(), Goal.target_date.asc(), Goal.created_at.desc()).all()
    return render_template("goals.html", goals=goal_list)


@app.post("/goals/<int:goal_id>/edit")
@login_required
def edit_goal(goal_id):
    goal = user_goal_or_404(goal_id)
    try:
        goal_from_form(goal)
        db.session.commit()
        flash("Goal updated.", "success")
    except ValueError as error:
        flash(str(error), "danger")
    return redirect(url_for("goals"))


@app.post("/goals/<int:goal_id>/toggle")
@login_required
def toggle_goal(goal_id):
    goal = user_goal_or_404(goal_id)
    goal.completed = not goal.completed
    goal.progress = 100 if goal.completed else min(goal.progress, 99)
    db.session.commit()
    flash("Goal marked complete." if goal.completed else "Goal reopened.", "success")
    return redirect(url_for("goals"))


@app.post("/goals/<int:goal_id>/delete")
@login_required
def delete_goal(goal_id):
    goal = user_goal_or_404(goal_id)
    db.session.delete(goal)
    db.session.commit()
    flash("Goal deleted.", "success")
    return redirect(url_for("goals"))


@app.route("/timetable", methods=["GET", "POST"])
@login_required
def timetable():
    user = get_current_user()
    if request.method == "POST":
        entry = TimetableEntry(user_id=user.id)
        try:
            timetable_from_form(entry)
            db.session.add(entry)
            db.session.commit()
            flash("Class added to your timetable.", "success")
        except ValueError as error:
            flash(str(error), "danger")
        return redirect(url_for("timetable"))
    entries = TimetableEntry.query.filter_by(user_id=user.id).order_by(TimetableEntry.day, TimetableEntry.start_time).all()
    return render_template("timetable.html", entries=entries)


@app.post("/timetable/<int:entry_id>/edit")
@login_required
def edit_timetable_entry(entry_id):
    entry = user_timetable_entry_or_404(entry_id)
    try:
        timetable_from_form(entry)
        db.session.commit()
        flash("Timetable entry updated.", "success")
    except ValueError as error:
        flash(str(error), "danger")
    return redirect(url_for("timetable"))


@app.post("/timetable/<int:entry_id>/delete")
@login_required
def delete_timetable_entry(entry_id):
    entry = user_timetable_entry_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash("Timetable entry deleted.", "success")
    return redirect(url_for("timetable"))


@app.route("/progress")
@login_required
def progress():
    user = get_current_user()
    assignments = Assignment.query.filter_by(user_id=user.id).all()
    goals = Goal.query.filter_by(user_id=user.id).all()
    notes_count = Note.query.filter_by(user_id=user.id).count()
    completed_assignments = sum(assignment.completed for assignment in assignments)
    completed_goals = sum(goal.completed for goal in goals)
    goal_progress = round(sum(goal.progress for goal in goals) / len(goals)) if goals else 0
    achievements = []
    if completed_assignments:
        achievements.append(f"Completed {completed_assignments} assignment{'s' if completed_assignments != 1 else ''}")
    if completed_goals:
        achievements.append(f"Achieved {completed_goals} goal{'s' if completed_goals != 1 else ''}")
    if notes_count:
        achievements.append(f"Saved {notes_count} note{'s' if notes_count != 1 else ''}")
    return render_template(
        "progress.html", total_assignments=len(assignments),
        completed_assignments=completed_assignments,
        pending_assignments=len(assignments) - completed_assignments,
        completed_goals=completed_goals, notes_count=notes_count,
        assignment_progress=percentage(completed_assignments, len(assignments)),
        goal_progress=goal_progress, achievements=achievements,
    )


@app.route("/pomodoro")
@login_required
def pomodoro():
    return render_template("pomodoro.html")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = get_current_user()
    if request.method == "POST":
        try:
            name = form_text("name", "Name", 100)
            email = form_text("email", "Email", 255).lower()
            if "@" not in email or email.startswith("@") or email.endswith("@"):
                raise ValueError("Please enter a valid email address.")
            other_user = User.query.filter(User.email == email, User.id != user.id).first()
            if other_user:
                raise ValueError("Another account already uses that email.")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")
            if new_password or confirm_password:
                if len(new_password) < 8:
                    raise ValueError("New password must be at least 8 characters long.")
                if new_password != confirm_password:
                    raise ValueError("New passwords do not match.")
                user.password_hash = generate_password_hash(new_password)
            user.name = name
            user.email = email
            db.session.commit()
            flash("Profile updated.", "success")
        except ValueError as error:
            flash(str(error), "danger")
        return redirect(url_for("profile"))
    return render_template(
        "profile.html",
        assignments_count=Assignment.query.filter_by(user_id=user.id).count(),
        notes_count=Note.query.filter_by(user_id=user.id).count(),
        goals_count=Goal.query.filter_by(user_id=user.id).count(),
    )


def prepare_database():
    """Create tables and make the original assignment-only demo database usable."""
    db.create_all()
    inspector = inspect(db.engine)
    if "assignment" not in inspector.get_table_names():
        return
    column_names = {column["name"] for column in inspector.get_columns("assignment")}
    with db.engine.begin() as connection:
        if "user_id" not in column_names:
            connection.execute(text("ALTER TABLE assignment ADD COLUMN user_id INTEGER"))
        if "created_at" not in column_names:
            connection.execute(text("ALTER TABLE assignment ADD COLUMN created_at DATETIME"))
            connection.execute(text("UPDATE assignment SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))


@app.cli.command("init-db")
def init_db_command():
    """Create the SQLite tables for a new installation."""
    prepare_database()
    print("Database tables are ready.")


with app.app_context():
    prepare_database()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
