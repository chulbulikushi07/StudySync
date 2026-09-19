# StudySync

StudySync is a Flask student-productivity application for managing assignments, notes, goals, and a weekly timetable in one place. Every account has its own private data.

## Features

- Secure registration, login, logout, password updates, and CSRF-protected forms
- Assignment CRUD, completion tracking, priorities, due dates, and filtering
- Notes CRUD with subject and category search
- Goals with target dates and progress tracking
- Timetable CRUD for weekly classes
- Live dashboard and progress statistics from stored data
- Protected administrator view of registered users and their record counts
- Browser-based Pomodoro timer

## Tech stack

- Python, Flask, Flask-SQLAlchemy
- SQLite for local development; PostgreSQL for Vercel deployment
- HTML5, Bootstrap 5, Bootstrap Icons, Jinja2

## Project structure

~~~text
app.py                 Flask routes, models, validation, and database setup
templates/             Jinja templates and Bootstrap views
public/static/         Vercel-compatible CSS and image assets
instance/              Local SQLite database (ignored by Git)
tests/                 Automated backend tests
vercel.json            Vercel function configuration
~~~

## Run locally

1. Create and activate a virtual environment:

   ~~~powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ~~~

2. Install the dependencies:

   ~~~powershell
   pip install -r requirements.txt
   ~~~

3. Set a development secret:

   ~~~powershell
   $env:SECRET_KEY = "replace-with-a-long-random-secret"
   ~~~

4. Start the app:

   ~~~powershell
   python app.py
   ~~~

Open http://127.0.0.1:5000. The local SQLite database is created automatically at instance/studysync.db.

## Environment variables

| Variable | Purpose |
| --- | --- |
| SECRET_KEY | Required unique secret for deployed instances. |
| DATABASE_URL | Hosted PostgreSQL URL for Vercel; omitted locally to use SQLite. |
| ADMIN_EMAIL | Optional email address that receives the administrator role. |
| FLASK_DEBUG | Set to 1 only for local debugging. |
| CSRF_ENABLED | Defaults to true; set to false only in controlled automated tests. |

Without ADMIN_EMAIL, the first locally registered account becomes the administrator. For a public deployment, set ADMIN_EMAIL before allowing registration.

## Deploy to Vercel

1. Create a hosted PostgreSQL database, such as Neon or Supabase, and copy its connection URL.
2. Import the GitHub repository into Vercel. Vercel detects the root app.py Flask entry point.
3. In Vercel Project Settings → Environment Variables, add:

   - DATABASE_URL: the PostgreSQL connection URL
   - SECRET_KEY: a long random value
   - ADMIN_EMAIL: your email address

4. Deploy. The application creates its tables automatically when it first connects to the database.

Vercel cannot use the local SQLite database because serverless storage is not persistent. The app therefore requires DATABASE_URL on Vercel and automatically converts standard Postgres URLs to the psycopg SQLAlchemy format.

## Deployment notes

The public/static directory is served as static content by Vercel. Local development and non-Vercel deployments can continue to use Flask's normal static route. For a traditional Linux host, set DATABASE_URL and run:

~~~bash
gunicorn --bind 0.0.0.0:8000 app:app
~~~

## Future improvements

- Password-reset emails
- Calendar export and assignment reminders
- Persisted Pomodoro history
- Formal database migrations for long-lived production schemas
