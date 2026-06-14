# Workflow — PPM Back-end 2026 Project
## Django Full-Stack Event Management System

Use this file as the practical execution plan for Codex in VS Code.

---

# Global Strategy

Build the project in small, verifiable steps.

Primary goal:

```txt
A complete Django Full-Stack Web Application, testable from browser, with demo users, realistic data, permissions, deployment, and README.
```

Do not start from Docker or REST API.

Order of priority:

1. Django project works locally.
2. Core models and migrations are correct.
3. Browser workflows work.
4. Roles and permissions work.
5. Demo database and README are complete.
6. Deployment works.
7. Docker or REST API only if time remains.

---

# Phase 0 — Project Setup

## Goal

Create a clean Django project skeleton.

## Codex prompt

```txt
Create a clean Django project for a PPM Back-end course project.

Project type: Full-Stack Web Application.
Framework: Django.
Track: Event Management System.
Apps required: accounts and events.
Use server-rendered templates, Bootstrap 5, Django auth, Django forms, Django messages, SQLite.

Create the initial project structure, requirements.txt, .gitignore, templates/base.html, app urls.py files, and project urls.py.

Do not implement business logic yet.
Do not add Docker yet.
Do not add REST API yet.
Keep the code minimal and runnable.
```

## Manual check

Run:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open:

```txt
http://127.0.0.1:8000/
```

---

# Phase 1 — Models and Admin

## Goal

Create the core data model.

Recommended models:

- `Profile`
- `Event`
- `Registration`
- optionally `Category`

## Codex prompt

```txt
Implement the core models for the Event Management System.

Requirements:
- Use Django ORM.
- Use AUTH_USER_MODEL references correctly.
- Add Profile linked one-to-one to User.
- Add Event with organizer ForeignKey to User.
- Add Registration linking attendee User to Event.
- Add useful fields for event title, description, date/time, location, capacity, category/status if useful.
- Add __str__ to every model.
- Add get_absolute_url to Event.
- Avoid null=True on CharField/TextField.
- Add uniqueness constraint to avoid duplicate registrations for the same user and event.
- Register models in admin with useful list_display, search_fields, list_filter.

Do not implement views yet.
```

## Manual check

Run:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open admin:

```txt
http://127.0.0.1:8000/admin/
```

Verify that models appear and can be created.

---

# Phase 2 — Authentication and Roles

## Goal

Set up login/logout and demo roles.

## Codex prompt

```txt
Implement authentication and roles.

Requirements:
- Use Django built-in auth views for login/logout.
- Add login/logout URLs and templates under templates/registration/.
- Configure LOGIN_URL, LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL.
- Create role logic for Attendee and Organizer.
- Use Django Groups named Attendee and Organizer.
- Add helper methods/properties where useful, but keep the source of truth clear.
- Add a management command or seed script to create demo users, groups, events, and registrations.
- Demo users:
  - admin_demo / admin12345
  - attendee_demo / attendee12345
  - organizer_demo / organizer12345
- Do not use personal passwords.
```

## Manual check

Run:

```bash
python manage.py seed_demo
python manage.py runserver
```

Test:

- login as attendee;
- logout;
- login as organizer;
- admin can access admin site.

---

# Phase 3 — Public Event Pages

## Goal

Create the read-only browser experience.

## Codex prompt

```txt
Implement public event browsing.

Requirements:
- Event list page.
- Event detail page.
- URLs must be named and namespaced.
- Use class-based views where appropriate.
- Use Bootstrap in templates.
- Use template inheritance from base.html.
- Use {% url %}; do not hardcode internal URLs.
- Show useful event fields.
- Show different navbar links for anonymous and authenticated users.
```

## Manual check

Open:

```txt
/
 /events/
 /events/<id>/
```

Check that pages render and links work.

---

# Phase 4 — Organizer CRUD

## Goal

Allow organizers to manage their events.

## Codex prompt

```txt
Implement organizer CRUD for Event.

Requirements:
- Organizer can create events.
- Organizer can update only own events.
- Organizer can delete only own events.
- Non-organizers cannot create events.
- Users cannot edit or delete events owned by others.
- Use LoginRequiredMixin and server-side authorization checks.
- Use ModelForm with explicit fields, never fields='__all__'.
- Use form_valid() to assign organizer=request.user.
- Use Django messages for success and permission-denied feedback.
- Use namespaced URLs and reverse_lazy/get_absolute_url.
```

## Manual check

Test:

1. Login as organizer_demo.
2. Create event.
3. Edit own event.
4. Delete own event.
5. Login as attendee_demo.
6. Try to access create/update/delete URLs.
7. Verify access is blocked.

---

# Phase 5 — Attendee Registration Workflow

## Goal

Allow attendees to register/unregister.

## Codex prompt

```txt
Implement attendee registration workflow.

Requirements:
- Authenticated Attendee can register for an event.
- Attendee can cancel own registration.
- Prevent duplicate registrations.
- Prevent registration when event is full, if capacity is implemented.
- Organizer should not register as attendee unless explicitly allowed by business rules.
- Add "My registrations" page for attendees.
- Add feedback messages for every action.
- Enforce permissions server-side.
```

## Manual check

Test:

1. Login as attendee_demo.
2. Register for an event.
3. Verify it appears in My registrations.
4. Cancel registration.
5. Try duplicate registration.
6. Try full event if capacity exists.

---

# Phase 6 — Organizer Attendee Management

## Goal

Let organizers inspect participants.

## Codex prompt

```txt
Implement organizer attendee management.

Requirements:
- Organizer can view list of attendees for events they own.
- Organizer cannot view attendee lists for events owned by other organizers.
- Add a clear link from "My events" or event detail.
- Use server-side queryset filtering.
- Use Bootstrap tables.
- Add messages/permission handling.
```

## Manual check

Test:

1. Login as organizer_demo.
2. Open own event attendee list.
3. Try to open another organizer's attendee list.
4. Verify access is denied.

---

# Phase 7 — Polish UI and UX

## Goal

Make the app look finished.

## Codex prompt

```txt
Polish the UI and UX.

Requirements:
- Improve base.html and navbar.
- Use Bootstrap consistently.
- Add clear empty states.
- Add badges for roles/status where useful.
- Show Django messages prominently.
- Make forms clean and readable.
- Ensure pages are responsive enough for normal browser testing.
- Do not add complex frontend frameworks.
```

## Manual check

Browse the whole site as:

- anonymous user;
- attendee;
- organizer;
- admin.

---

# Phase 8 — Tests and Quality Check

## Goal

Catch obvious regressions.

## Codex prompt

```txt
Add practical tests for the core project.

Requirements:
- Test event list/detail pages.
- Test login-required pages.
- Test organizer-only create/update/delete behavior.
- Test attendee registration and duplicate prevention.
- Test ownership protection.
- Keep tests understandable and maintainable.
```

## Manual check

Run:

```bash
python manage.py test
python manage.py check
```

Also run:

```bash
python manage.py makemigrations --check
```

---

# Phase 9 — README and Demo Data

## Goal

Make the project immediately testable by the instructor.

## Codex prompt

```txt
Write a complete README.md for the project.

Requirements:
- Project title and student names placeholder.
- Project type: Full-Stack Web Application.
- Framework: Django.
- Track: Event Management System.
- Feature list grouped by role.
- Local installation instructions.
- Mention db.sqlite3 is included and populated.
- Demo accounts with username/password/role.
- Deployment link placeholder.
- Browser-based testing scenario step-by-step.
- Do not mention features that are not implemented.
```

## Manual check

Follow the README from a clean clone or fresh folder.

---

# Phase 10 — Deployment

## Goal

Deploy the working app.

Recommended order:

1. Make local version fully working.
2. Choose Render/Railway/PythonAnywhere.
3. Configure environment variables.
4. Configure static files.
5. Deploy.
6. Test demo scenario on deployed URL.
7. Update README with real URL.

## Codex prompt

```txt
Prepare this Django app for production deployment.

Requirements:
- Add gunicorn if needed.
- Add whitenoise if needed for static files.
- Read SECRET_KEY, DEBUG, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS from environment where appropriate.
- Keep local development easy.
- Do not break SQLite demo database in the repository.
- Add deployment notes to README.
```

## Manual check

Check deployed site:

- homepage;
- static CSS;
- login;
- attendee workflow;
- organizer workflow;
- admin access if needed.

---

# Optional Phase 11 — Docker

Only do this after the deployed app works.

## Codex prompt

```txt
Add optional Docker support to the working Django project.

Requirements:
- Dockerfile with python:3.12-slim or equivalent pinned image.
- .dockerignore.
- docker-compose.yml without deprecated version key.
- Non-root user if feasible.
- Exec-form CMD.
- Makefile targets for docker-build, docker-up, docker-down.
- Do not break non-Docker local setup.
- Update README with Docker instructions.
```

---

# Optional Phase 12 — REST API

Only do this after the Full-Stack project is finished.

## Codex prompt

```txt
Add a small optional Django REST Framework API for the Event model.

Requirements:
- Add djangorestframework to requirements.
- Add rest_framework to INSTALLED_APPS.
- Add serializers.py.
- Add API URLs under /api/.
- Add read-only event list/detail endpoints first.
- Add permissions if write endpoints are added.
- Do not replace the Full-Stack browser workflow.
- Document endpoints in README only if they work.
```

---

# Final Rule

Before submitting, run the browser scenario exactly as written in README.

If the README says the professor can do something, it must work on the deployed version.
