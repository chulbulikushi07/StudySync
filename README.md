# 📚 StudySync

**🔗 Live app: [study-sync-ruddy-seven.vercel.app](https://study-sync-ruddy-seven.vercel.app/)**

**StudySync** is a Flask web app that helps students stay organised. Manage assignments, notes, goals, and a weekly timetable in one place, track your progress on a live dashboard, and focus with a built-in Pomodoro timer. Every account's data is private to that user.

## Features

- **Accounts & security**: registration, login/logout, password updates, hashed passwords, and CSRF-protected forms
- **Assignments**: create, edit, delete, mark complete, set priority and due date, and filter the list
- **Notes**: full CRUD with subject and category search
- **Goals**: target dates and progress tracking
- **Timetable**: weekly class schedule with full CRUD
- **Dashboard & progress**: live statistics computed from your stored data
- **Pomodoro timer**: browser-based focus timer
- **Admin view**: protected page listing registered users and their record counts
- **Data isolation**: users can only access their own records (covered by tests)

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.13, Flask 3, Flask-SQLAlchemy 3 |
| Database | SQLite (local), PostgreSQL via `psycopg` (production) |
| Frontend | Jinja2, HTML5, Bootstrap 5, Bootstrap Icons |
| Hosting | Vercel (serverless) or any host running Gunicorn |

## Project structure

```text
StudySync/
├── app.py              # Routes, models, validation, and database setup
├── templates/          # Jinja2 templates (base layouts + one per page)
├── public/static/      # CSS and images (served as static files on Vercel)
├── tests/test_app.py   # End-to-end backend tests
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel function configuration
└── instance/           # Local SQLite database (created automatically, git-ignored)
```

## Getting started

### Prerequisites

- Python 3.13 (see `.python-version`)
- `pip`

### Installation

1. **Clone the repository and enter it**

```bash
   git clone https://github.com/chulbulikushi07/StudySync.git
   cd StudySync
```

2. **Create and activate a virtual environment**

```bash
   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
```

```powershell
   # Windows (PowerShell)
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
```

3. **Install dependencies**

```bash
   pip install -r requirements.txt
```

4. **Set a secret key**

```bash
   # macOS / Linux
   export SECRET_KEY="replace-with-a-long-random-secret"
```

```powershell
   # Windows (PowerShell)
   $env:SECRET_KEY = "replace-with-a-long-random-secret"
```

5. **Run the app**

```bash
   python app.py
```

Open [(https://study-sync-ruddy-seven.vercel.app/)]. The SQLite database is created automatically at `instance/studysync.db`. You can also create the tables manually with `flask --app app init-db`.

> **Tip:** without `ADMIN_EMAIL` set, the **first account registered** becomes the administrator.

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `SECRET_KEY` | Yes on Vercel | Secret used to sign sessions. Use a long, random value in production. |
| `DATABASE_URL` | Yes on Vercel | PostgreSQL connection URL. Leave unset locally to use SQLite. `postgres://` and `postgresql://` URLs are converted to the `psycopg` format automatically. |
| `ADMIN_EMAIL` | Recommended | Email address that receives the administrator role when it registers. |
| `FLASK_DEBUG` | No | Set to `1` for local debugging only. |
| `CSRF_ENABLED` | No | Defaults to `true`. Set to `false` only in controlled automated tests. |

## Running the tests

```bash
python -m unittest tests.test_app
```

The tests use a temporary SQLite database and cover authentication, protected pages, CRUD for each resource, the live dashboard, per-user data isolation, profile and password changes, and input validation.

## Deployment

### Vercel

1. Create a hosted PostgreSQL database (for example on [Neon](https://neon.tech) or [Supabase](https://supabase.com)) and copy its connection URL.
2. Import the GitHub repository into Vercel. It detects the Flask entry point `app.py`.
3. Under **Project Settings → Environment Variables**, add `DATABASE_URL`, `SECRET_KEY`, and `ADMIN_EMAIL`.
4. Deploy. Tables are created automatically on first connection.

The app refuses to start on Vercel if `DATABASE_URL` or `SECRET_KEY` is missing, because serverless storage is not persistent and SQLite cannot be used there. **Set `ADMIN_EMAIL` before opening registration** so the first visitor doesn't become admin.

### Traditional Linux host

```bash
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
export SECRET_KEY="a-long-random-secret"
gunicorn --bind 0.0.0.0:8000 app:app
```

## Roadmap

- Password-reset emails
- Calendar export and assignment reminders
- Persisted Pomodoro history
- Formal database migrations (e.g. Alembic) for long-lived production schemas

## Contributing

Issues and pull requests are welcome. Please run the test suite before submitting changes.

## License

Released under the MIT License. See [LICENSE](LICENSE).
