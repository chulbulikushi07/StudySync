"""End-to-end checks for the most important StudySync workflows."""

import os
import tempfile
import unittest
from pathlib import Path


TEST_DB = Path(tempfile.gettempdir()) / "studysync_test.sqlite"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key"

from app import Assignment, Goal, Note, TimetableEntry, User, app, db  # noqa: E402


class StudySyncTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()

    def post(self, url, data=None, **kwargs):
        """Submit a form with the same CSRF token a browser would send."""
        with self.client.session_transaction() as browser_session:
            token = browser_session.get("_csrf_token", "test-csrf-token")
            browser_session["_csrf_token"] = token
        values = {"csrf_token": token}
        values.update(data or {})
        return self.client.post(url, data=values, **kwargs)

    def register(self, name="Ada", email="ada@example.com", password="strongpass"):
        return self.post(
            "/register",
            {
                "name": name,
                "email": email,
                "password": password,
                "confirm_password": password,
            },
        )

    def login(self, email="ada@example.com", password="strongpass"):
        return self.post("/login", {"email": email, "password": password})

    def assignment_data(self, title="Essay"):
        return {
            "title": title,
            "subject": "English",
            "due_date": "2030-02-01",
            "priority": "High",
            "description": "Write a structured essay.",
        }

    def test_authentication_and_protected_pages(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

        self.assertEqual(self.register().status_code, 302)
        self.assertEqual(self.client.get("/dashboard").status_code, 200)
        with app.app_context():
            self.assertEqual(User.query.count(), 1)
            self.assertNotEqual(User.query.first().password_hash, "strongpass")
            self.assertTrue(User.query.first().is_admin)
        self.assertEqual(self.client.get("/admin/users").status_code, 200)

        self.assertEqual(self.post("/logout").status_code, 302)
        self.assertEqual(self.login().status_code, 302)
        self.assertEqual(self.client.get("/profile").status_code, 200)

    def test_productivity_crud_and_live_dashboard(self):
        self.register()

        self.assertEqual(self.post("/assignments", self.assignment_data()).status_code, 302)
        with app.app_context():
            assignment = Assignment.query.one()
            assignment_id = assignment.id
        updated_assignment = self.assignment_data("Final Essay")
        updated_assignment["priority"] = "Medium"
        self.post(f"/assignments/{assignment_id}/edit", updated_assignment)
        self.post(f"/assignments/{assignment_id}/toggle")

        note_data = {
            "title": "Formula sheet",
            "subject": "Mathematics",
            "category": "Revision",
            "content": "Derivative and integral formulas.",
        }
        self.post("/notes", note_data)
        with app.app_context():
            note_id = Note.query.one().id
        note_data["title"] = "Updated formula sheet"
        self.post(f"/notes/{note_id}/edit", note_data)

        goal_data = {
            "title": "Finish project",
            "goal_type": "Semester",
            "target_date": "2030-03-01",
            "progress": "60",
            "description": "Finish the final project.",
        }
        self.post("/goals", goal_data)
        with app.app_context():
            goal_id = Goal.query.one().id
        self.post(f"/goals/{goal_id}/toggle")

        timetable_data = {
            "class_name": "Calculus 101",
            "subject": "Mathematics",
            "day": "Monday",
            "start_time": "09:00",
            "end_time": "10:00",
            "room": "A-101",
            "instructor": "Professor Ada",
        }
        self.post("/timetable", timetable_data)
        with app.app_context():
            entry_id = TimetableEntry.query.one().id
        timetable_data["room"] = "A-102"
        self.post(f"/timetable/{entry_id}/edit", timetable_data)

        dashboard = self.client.get("/dashboard")
        progress = self.client.get("/progress")
        self.assertIn(b"Completed", dashboard.data)
        self.assertIn(b"Final Essay", self.client.get("/assignments").data)
        self.assertIn(b"Tasks Completed", progress.data)
        for page in ("/notes", "/goals", "/timetable", "/pomodoro", "/profile"):
            self.assertEqual(self.client.get(page).status_code, 200)
        with app.app_context():
            self.assertTrue(Assignment.query.one().completed)
            self.assertEqual(Note.query.one().title, "Updated formula sheet")
            self.assertTrue(Goal.query.one().completed)
            self.assertEqual(TimetableEntry.query.one().room, "A-102")

        self.post(f"/assignments/{assignment_id}/delete")
        self.post(f"/notes/{note_id}/delete")
        self.post(f"/goals/{goal_id}/delete")
        self.post(f"/timetable/{entry_id}/delete")
        with app.app_context():
            self.assertEqual(Assignment.query.count(), 0)
            self.assertEqual(Note.query.count(), 0)
            self.assertEqual(Goal.query.count(), 0)
            self.assertEqual(TimetableEntry.query.count(), 0)

    def test_users_cannot_access_each_others_data(self):
        self.register("First user", "first@example.com")
        self.post("/assignments", self.assignment_data("Private assignment"))
        with app.app_context():
            assignment_id = Assignment.query.one().id

        self.post("/logout")
        self.register("Second user", "second@example.com")
        assignments_page = self.client.get("/assignments")
        self.assertNotIn(b"Private assignment", assignments_page.data)
        self.assertEqual(self.client.get("/admin/users").status_code, 403)
        response = self.post(f"/assignments/{assignment_id}/toggle")
        self.assertEqual(response.status_code, 404)

    def test_profile_password_and_validation(self):
        self.register()
        invalid_time = {
            "class_name": "Invalid class",
            "subject": "Physics",
            "day": "Monday",
            "start_time": "11:00",
            "end_time": "10:00",
            "room": "",
            "instructor": "",
        }
        response = self.post("/timetable", invalid_time, follow_redirects=True)
        self.assertIn(b"End time must be later than start time.", response.data)

        self.post(
            "/profile",
            {
                "name": "Ada Lovelace",
                "email": "ada.lovelace@example.com",
                "new_password": "newstrongpass",
                "confirm_password": "newstrongpass",
            },
        )
        self.post("/logout")
        self.assertEqual(self.login("ada.lovelace@example.com", "newstrongpass").status_code, 302)


if __name__ == "__main__":
    unittest.main()
