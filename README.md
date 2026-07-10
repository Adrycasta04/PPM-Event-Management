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

## Evaluation links

- **Live application:** [https://ppm-events.onrender.com](https://ppm-events.onrender.com)
- **Demo accounts:** [View credentials](#demo-accounts)
- **Testing scenario:** [Open the browser-based walkthrough](#browser-based-testing-scenario)

## 📌 Project overview

PPM Events is a server-rendered Django application for university and student
community events. It supports publishing workshops, seminars, study
activities, career events, sport, social and cultural activities while
separating the workflows of attendees and organizers.

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
- browse published university and student community events;
- search events by title, description or location;
- filter events by category and time period;
- open the detail page of a published event;
- open an organizer profile and browse their published event history;
- read participant reviews of completed events;
- access the login and sign-up pages.

Draft and cancelled events are not visible in the public event list.

### Attendee

- login and logout;
- browse published events;
- use event search, category filtering and time filtering;
- save and remove favorite events;
- view the `My favorites` page;
- browse an organizer's upcoming and past published events;
- register for an event with available capacity;
- cancel an owned registration;
- view the `My registrations` page;
- review a completed event after participating;
- update or delete an owned review;
- receive clear messages for duplicate registrations and full events.

Attendees cannot access organizer CRUD pages or attendee lists.

### Organizer

- login and logout;
- use attendee features, including event registration;
- create events;
- view all owned events, including drafts and cancelled events;
- update or delete only owned events;
- view registrations and attendee details for owned events;
- monitor registrations against event capacity.

Organizers cannot modify, delete or inspect attendees for events owned by
another organizer.

### Admin

- access Django Admin;
- use attendee and organizer features;
- manage all events from the frontend;
- manage users, groups, profiles, categories, events, registrations,
  favorites and reviews from Django Admin.

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

- 11 published events with varied student community activities;
- published events with available capacity;
- a published event at full capacity;
- a published event without participants;
- university and student community activities across technology, study,
  career, sport, social and cultural contexts;
- eight persisted event categories available in discovery and event forms;
- a draft event;
- two cancelled events;
- events owned by two different organizers;
- existing registrations for attendee accounts and one organizer account;
- four demo favorites;
- three reviews attached only to completed events and registered participants.

Notable events:

- `Django Workshop for Beginners`: published, places available, existing
  attendees;
- `AI & Machine Learning Seminar`: published university seminar;
- `Hackathon: Build for Campus`: published with an organizer registration;
- `CV and LinkedIn Lab`: published and full;
- `Erasmus Welcome Aperitivo`: published with no initial registrations;
- `Student Five-a-Side Tournament`: published sport event;
- `Algorithms Study Group`: published study activity;
- `Summer Student Party`: published social evening;
- `Photography Walk in Florence`: completed cultural activity with demo
  registrations and reviews;
- `International Students Meetup`: published and owned by
  `organizer2_demo`;
- `Cinema Night at the Student Union`: completed cultural event with a demo
  review;
- `UNIFI Career Day - Cancelled`: not publicly visible;
- `Student Radio Podcast Lab - Draft`: not publicly visible;
- `Campus Volunteering Fair - Cancelled`: not publicly visible.

## 🧪 Testing

### Browser-based testing scenario

1. Open the homepage and select `Events`.
2. Search for `Django`, select the `Technology` category or filter by
   `This month`, and verify that only matching published events appear.
3. Verify that only published events appear.
4. Open `CV and LinkedIn Lab` and verify that its capacity is full.
5. Log in as `attendee_demo / attendee12345`.
6. Open `Erasmus Welcome Aperitivo` and register.
7. Add the event to favorites and verify it appears under `Favorites`.
8. Open `My registrations` and verify that the new registration appears.
9. Open the completed `Photography Walk in Florence` event and verify that
   participant reviews are visible and the owned review can be updated.
10. Select the organizer name and verify that their upcoming and past
    published events appear while Draft and Cancelled events do not.
11. Cancel the Erasmus Welcome registration.
12. Log out and log in as `organizer_demo / organizer12345`.
13. Open `Manage events`.
14. Create a new draft event with a category, then update its title and
    publish it.
15. Open the attendee list for `Django Workshop for Beginners` and verify
    that the two demo attendees are listed.
16. Open the public detail of `International Students Meetup`, which is
    owned by `organizer2_demo`, and verify that edit/delete actions are absent
    for another non-admin organizer.
17. Log out and log in as `organizer2_demo / organizer212345`.
18. Verify that `International Students Meetup` appears in `Manage events`
    while events owned by `organizer_demo` do not.
19. Log in as `admin_demo / admin12345`, open `Manage events`, and verify that
    all events are available from the frontend.
20. Open `/admin/` to verify full Django administration access.

### Automated tests

Run the complete test suite:

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check
```

The tests cover authentication, roles, permissions, ownership, forms, model
constraints, event visibility, registration capacity, duplicate prevention,
event search, category and time filtering, favorites, review eligibility,
URL namespaces and representative query efficiency.

## 🔒 Security and authorization

- all write forms use CSRF protection;
- authentication uses Django built-in auth;
- role and ownership checks are enforced server-side;
- event registrations are protected by a database uniqueness constraint;
- favorites and reviews are protected by database uniqueness constraints;
- reviews require a completed event and an existing registration;
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
