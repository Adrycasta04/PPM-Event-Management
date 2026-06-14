# PPM Events

**Student:** `[Nome e Cognome - inserire prima della consegna]`  
**Course:** Progettazione e Produzione Multimediale - Back-end 2026  
**Project type:** Full-Stack Web Application  
**Framework:** Django 5.2 LTS  
**Track:** Event Management System

## Description

PPM Events is a server-rendered Django application for publishing events,
managing registrations and separating the workflows of attendees and
organizers.

The application uses Django ORM, Forms, Templates, built-in authentication,
Groups, server-side authorization checks, Bootstrap 5 and SQLite. It does not
require a separate frontend or REST client and can be tested entirely from a
browser.

## Features by role

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

## Main technologies

- Python 3.12 recommended
- Django 5.2.15
- SQLite
- Bootstrap 5
- Django Templates
- Django built-in authentication and Groups

## Local installation

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

## SQLite demo database

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

## Demo accounts

| Username | Password | Role |
|---|---|---|
| `admin_demo` | `admin12345` | Admin / superuser |
| `attendee_demo` | `attendee12345` | Attendee |
| `attendee2_demo` | `attendee212345` | Attendee |
| `organizer_demo` | `organizer12345` | Organizer |
| `organizer2_demo` | `organizer212345` | Organizer |

These credentials are intentionally public demo credentials and are not used
for personal or production accounts.

## Included demo scenarios

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

## Browser-based testing scenario

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

## Automated tests

Run the complete test suite:

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check
```

The tests cover authentication, roles, permissions, ownership, forms, model
constraints, event visibility, registration capacity, duplicate prevention,
URL namespaces and representative query efficiency.

## Security and authorization

- all write forms use CSRF protection;
- authentication uses Django built-in auth;
- role and ownership checks are enforced server-side;
- event registrations are protected by a database uniqueness constraint;
- event capacity and date consistency are validated;
- secrets are not committed;
- internal URLs use Django URL names and reversing.

## Deployment

**Deployment URL:** `[TO BE ADDED IN PHASE 10]`

Production deployment configuration and the final online URL will be added in
Phase 10.
