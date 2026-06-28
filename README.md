# PPM Events

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django 5.2 LTS](https://img.shields.io/badge/Django-5.2_LTS-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)
[![Render deployment](https://img.shields.io/badge/Render-Live-46E3B7?logo=render&logoColor=white)](https://ppm-events.onrender.com)

| Project information | Details |
|---|---|
| **Student** | Adriano Castaldo |
| **Course** | Progettazione e Produzione Multimediale - Back-end 2026 |
| **Project type** | Full-Stack Web Application |
| **Framework** | Django 5.2 LTS |
| **Track** | Event Management System |

## 📌 Project overview

PPM Events is a server-rendered Django application for publishing events,
managing registrations and separating the workflows of attendees and
organizers.

The application uses Django ORM, Forms, Templates, built-in authentication,
Groups, server-side authorization checks, Bootstrap 5 and SQLite. It does not
require a separate frontend or REST client and can be tested entirely from a
browser.

### Main technologies

- Python 3.12 recommended
- Django 5.2.15
- Gunicorn 26.0.0
- WhiteNoise 6.12.0
- SQLite
- Bootstrap 5
- Django Templates
- Django built-in authentication and Groups

## 👥 Features by role

### Anonymous user

- view the homepage;
- browse published events;
- open the detail page of a published event;
- access the login page.

Draft and cancelled events are not visible in the public event list.

### Attendee

- login and logout;
- browse published events;
- register for an event with available capacity;
- cancel an owned registration;
- view the `My registrations` page;
- receive clear messages for duplicate registrations and full events.

Attendees cannot access organizer CRUD pages or attendee lists.

### Organizer

- login and logout;
- create events;
- view all owned events, including drafts and cancelled events;
- update or delete only owned events;
- view registrations and attendee details for owned events;
- monitor registrations against event capacity.

Organizers cannot modify, delete or inspect attendees for events owned by
another organizer.

### Admin

- access Django Admin;
- manage users, groups, profiles, events and registrations.

Admin status does not automatically grant the application-specific Attendee or
Organizer role.

## Local setup and demo data

### Local installation

```bash
git clone <repository-url>
cd ppm-event-management
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
source .venv/bin/activate
```

Install dependencies and prepare the database:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

### SQLite demo database

The repository includes a populated `db.sqlite3` containing demo users,
groups, profiles, events and registrations. No initial data entry is required
to test the application.

To recreate the deterministic demo dataset:

```bash
python manage.py seed_demo --reset
```

The `--reset` option deletes existing users and event data before recreating
the demo dataset. Run it only when a clean demo database is desired.

Running the command without `--reset` updates the demo dataset while leaving
unrelated application data intact:

```bash
python manage.py seed_demo
```

### Demo accounts

| Username | Password | Role |
|---|---|---|
| `admin_demo` | `admin12345` | Admin / superuser |
| `attendee_demo` | `attendee12345` | Attendee |
| `attendee2_demo` | `attendee212345` | Attendee |
| `organizer_demo` | `organizer12345` | Organizer |
| `organizer2_demo` | `organizer212345` | Organizer |

These credentials are intentionally public demo credentials and are not used
for personal or production accounts.

### Included demo scenarios

The database contains:

- published events with available capacity;
- a published event at full capacity;
- a published event without participants;
- a draft event;
- a cancelled event;
- events owned by two different organizers;
- existing registrations for both attendee accounts.

Notable events:

- `Django Community Meetup Firenze`: published, places available, existing
  attendees;
- `Workshop di Fotografia Urbana`: published and full;
- `Open Day Produzione Multimediale`: published with no initial registrations;
- `Festival Audio-Visuale Estate 2026`: published and owned by
  `organizer2_demo`;
- `Laboratorio Podcast - Bozza`: not publicly visible;
- `Rassegna Cinema all'Aperto - Annullata`: not publicly visible.

## 🧪 Testing

### Browser-based testing scenario

1. Open the homepage and select `Eventi`.
2. Verify that only published events appear.
3. Open `Workshop di Fotografia Urbana` and verify that its capacity is full.
4. Log in as `attendee_demo / attendee12345`.
5. Open `Open Day Produzione Multimediale` and register.
6. Open `Le mie iscrizioni` and verify that the new registration appears.
7. Cancel the Open Day registration.
8. Log out and log in as `organizer_demo / organizer12345`.
9. Open `I miei eventi`.
10. Create a new draft event, then update its title and publish it.
11. Open the attendee list for `Django Community Meetup Firenze`.
12. Verify that the two demo attendees are listed.
13. Open the public detail of `Festival Audio-Visuale Estate 2026`, which is
    owned by `organizer2_demo`, and verify that edit/delete actions are absent.
14. Log out and log in as `organizer2_demo / organizer212345`.
15. Verify that `Festival Audio-Visuale Estate 2026` appears in `I miei eventi`
    while events owned by `organizer_demo` do not.
16. Log in as `admin_demo / admin12345` and open `/admin/`.

### Automated tests

Run the complete test suite:

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check
```

The tests cover authentication, roles, permissions, ownership, forms, model
constraints, event visibility, registration capacity, duplicate prevention,
URL namespaces and representative query efficiency.

## 🔒 Security and authorization

- all write forms use CSRF protection;
- authentication uses Django built-in auth;
- role and ownership checks are enforced server-side;
- event registrations are protected by a database uniqueness constraint;
- event capacity and date consistency are validated;
- secrets are not committed;
- internal URLs use Django URL names and reversing.

## Deployment

**Recommended platform:** Render

**Deployment URL:** https://ppm-events.onrender.com

The repository includes a Render Blueprint in `render.yaml` and a deployment
build script in `build.sh`.

### Render deployment

1. Push the final repository to GitHub.
2. Create a Render account and open **Blueprints**.
3. Select **New Blueprint Instance** and connect this repository.
4. Confirm creation of the `ppm-events` Python web service.
5. Wait for the build and deployment to complete.
6. Open the generated `.onrender.com` URL.
7. Run the complete browser-based testing scenario.

The Blueprint uses:

```text
Build command: bash build.sh
Start command: gunicorn django_project.wsgi:application --bind 0.0.0.0:$PORT
Health check path: /
```

The build script performs:

```bash
python -m pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

Render reads `.python-version` and uses the latest available Python 3.12 patch
release.

### Environment variables

The committed `render.yaml` configures:

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | Generated automatically by Render. Never commit its real value. |
| `DJANGO_DEBUG` | Yes | Set to `False` in production. |

The application also supports these optional variables:

| Variable | Example | Description |
|---|---|---|
| `DJANGO_ALLOWED_HOSTS` | `example.com,www.example.com` | Additional comma-separated hosts, useful for custom domains. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://example.com` | Additional comma-separated HTTPS origins for CSRF. |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` | Controls HTTPS redirect when `DEBUG=False`. |
| `DJANGO_SECURE_HSTS_SECONDS` | `3600` | HSTS duration in seconds; defaults to one hour in production. |

Render automatically supplies `RENDER_EXTERNAL_HOSTNAME`; the application adds
that hostname to `ALLOWED_HOSTS` and its HTTPS origin to
`CSRF_TRUSTED_ORIGINS`.

### SQLite persistence note

The deployed service starts with the populated `db.sqlite3` committed in this
repository, so all demo accounts and scenarios are immediately available.

Render free web services use an ephemeral filesystem. Browser changes work
during the running instance, but they can be reset to the committed demo
database after a restart or redeploy. This behavior is acceptable for the
course demo and keeps the repository SQLite-based as required.

Persistent production data would require a paid Render persistent disk or a
managed database. Neither is required for this academic deployment.
