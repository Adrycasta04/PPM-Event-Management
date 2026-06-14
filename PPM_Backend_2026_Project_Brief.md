# Project Brief — Back-end PPM 2026
## Full-Stack Django Web Application

**Course:** Progettazione e Produzione Multimediale (PPM) — Back-end  
**Instructor:** Simone Ricci — simone.ricci@unifi.it  
**Submission deadline:** 12/07/2026  
**Submission form:** https://forms.gle/SJE19bFLXxMTVd2EA  
**Target:** Build a complete, deployable, browser-testable Full-Stack Web Application compliant with the PPM Back-end project requirements.  
**Quality target:** 30L-level project: clean architecture, complete workflows, strong README, realistic demo data, correct permissions, and polished browser experience.

---

# 1. Project Type Decision

## Chosen project type

**Full-Stack Web Application**

The project must be usable directly from the browser through server-rendered HTML pages. The application must include:

- relational models;
- Django ORM;
- migrations;
- views;
- URL routing;
- templates;
- forms;
- authentication;
- role-based permissions;
- populated SQLite demo database;
- deployment URL;
- clear README with demo accounts and browser-based testing scenario.

## Not chosen

**REST API** is not the main project type.

REST endpoints may be added only as optional stretch goals after the Full-Stack application is complete. They must not replace the browser-based workflow required for evaluation.

---

# 2. Recommended Stack

## Main stack

- **Language:** Python 3.12
- **Framework:** Django
- **Database for repository:** SQLite, committed as `db.sqlite3`
- **Frontend:** Server-rendered HTML templates with Bootstrap 5
- **Forms:** Django `Form` / `ModelForm`
- **Authentication:** Django built-in authentication system
- **Authorization:** Django Groups, permissions, and explicit view-level checks
- **Deployment:** Render, Railway, PythonAnywhere, Heroku, or equivalent free/free-plan platform
- **Production server:** Gunicorn when applicable

## Useful dependencies

Use only if actually needed:

```txt
Django
gunicorn
python-dotenv
django-crispy-forms
crispy-bootstrap5
whitenoise
dj-database-url
psycopg2-binary
```

For a pure SQLite deployment, PostgreSQL-related packages are optional and should not be added unless production actually uses PostgreSQL.

---

# 3. Official Full-Stack Track

## Chosen track

**Event Management System**

Reason: it maps cleanly to Django Full-Stack features and is easy to test from the browser.

Minimum features:

- event list;
- event detail page;
- event creation;
- event update/delete by owner;
- event registration;
- attendee list;
- registration management.

Minimum roles:

- **Attendee**
  - view events;
  - register/unregister for events;
  - manage own registrations.

- **Organizer**
  - create events;
  - update/delete own events;
  - view attendees for own events;
  - manage registrations for own events where appropriate.

---

# 4. Core Academic Requirements

The project is valid only if all these requirements are satisfied.

## Repository

The GitHub repository must include:

- source code;
- `requirements.txt`;
- migrations;
- populated `db.sqlite3`;
- deployment-related files if used;
- `README.md`;
- no virtual environment;
- no private keys;
- no personal passwords;
- no unfinished placeholder features.

## Deployment

The application must be reachable online. The deployment URL must be clearly stated in the README.

## SQLite demo database

The repository must include a populated SQLite database:

```txt
db.sqlite3
```

It must contain enough demo data to test the main workflows without manually creating everything from zero.

## Demo accounts

The README must include at least one demo account for each relevant role.

Example:

```txt
admin_demo / admin12345 — superuser
attendee_demo / attendee12345 — Attendee
organizer_demo / organizer12345 — Organizer
```

Never use personal passwords, real accounts, private API keys, or sensitive data.

---

# 5. Django Architecture Rules

## Project structure

Use a modular Django structure with at least two apps.

Recommended structure:

```txt
project_root/
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3
├── .gitignore
├── django_project/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── migrations/
├── events/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   └── migrations/
├── templates/
│   ├── base.html
│   ├── includes/
│   ├── registration/
│   ├── accounts/
│   └── events/
└── static/
```

## Django apps

At minimum:

- `accounts` for authentication, profiles, roles, and user-related logic;
- `events` for the Event Management domain.

More apps are allowed only if they improve clarity.

---

# 6. Models and ORM Rules

## Relational model

Use a relational model with at least two meaningful relationships among:

- `ForeignKey`;
- `ManyToManyField`;
- `OneToOneField`.

Recommended model set:

- `User`;
- `Profile`;
- `Event`;
- `Registration`;
- optionally `Category`, `Venue`, or `Feedback`.

Recommended relationships:

- `Profile` → `User` via `OneToOneField`;
- `Event` → organizer `User` via `ForeignKey`;
- `Registration` → `Event` via `ForeignKey`;
- `Registration` → attendee `User` via `ForeignKey`.

## Model rules

Every model must define:

```python
def __str__(self):
    ...
```

Main models should define:

```python
def get_absolute_url(self):
    ...
```

Use `choices` for static options. Use relational tables for dynamic entities.

Do not use names that conflict with Django model methods or APIs, such as:

- `save`;
- `delete`;
- `clean`.

## Field rules

For textual fields:

```python
models.CharField(...)
models.TextField(...)
```

Avoid:

```python
null=True
```

Use `blank=True` only when the form may accept an empty value.

For strings, prefer empty string over database `NULL`, unless there is a precise reason.

---

# 7. User Model and Profiles

## Recommended approach

Use a custom user model based on `AbstractUser` only if needed early in the project.

Keep the custom user model minimal.

Recommended:

```python
class User(AbstractUser):
    pass
```

Then store application-specific data in a separate profile model:

```python
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=RoleChoices.choices)
```

## Required if using a custom user model

If a custom user model is created:

- define it before the first migration;
- set `AUTH_USER_MODEL` in `settings.py`;
- register it correctly in `admin.py`;
- avoid unnecessary custom manager complexity unless the login identifier or user creation flow really changes.

Do not create a complex custom authentication system unless required.

Use Django’s built-in authentication.

---

# 8. Authentication and Authorization

## Authentication

Use Django’s built-in authentication system.

Required:

- login;
- logout;
- protected pages;
- redirects after login/logout.

In `settings.py`, define:

```python
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "..."
LOGOUT_REDIRECT_URL = "..."
```

## Authorization

Authorization must be enforced server-side.

Never rely only on hiding buttons in templates.

Use:

- `LoginRequiredMixin`;
- `PermissionRequiredMixin` where useful;
- role checks;
- ownership checks;
- filtered querysets.

For object ownership:

```python
def get_queryset(self):
    return Event.objects.filter(organizer=self.request.user)
```

For write actions:

- only the owner/authorized role can update or delete;
- unauthorized users should receive a clear error or redirect with a message.

## Roles

Use Django Groups for role names, for example:

- `Attendee`;
- `Organizer`.

A user may also have a linked `Profile` with a role field if it simplifies application logic.

The source of truth must remain clear and consistent.

---

# 9. Views, URLs, and Routing

## URL rules

Each app must have its own `urls.py`.

Each app-level `urls.py` must define:

```python
app_name = "events"
```

All URLs must be named.

Use:

- `{% url 'namespace:name' %}` in templates;
- `reverse()` or `reverse_lazy()` in Python;
- `get_absolute_url()` in models where useful.

Avoid hardcoded URLs.

## Views

Prefer class-based views for CRUD workflows:

- `ListView`;
- `DetailView`;
- `CreateView`;
- `UpdateView`;
- `DeleteView`.

Override methods only when useful:

- `get_queryset()`;
- `get_context_data()`;
- `form_valid()`;
- `dispatch()`.

Use function-based views only when they make the logic simpler.

## CRUD requirement

At least one main resource must support full CRUD.

For this project, the main resource is:

```txt
Event
```

Required operations:

- create event;
- list events;
- view event detail;
- update own event;
- delete own event.

---

# 10. Forms

Use Django `Form` or `ModelForm`.

Do not create raw HTML forms disconnected from Django validation.

Every POST form must include:

```django
{% csrf_token %}
```

Use explicit fields.

Avoid:

```python
fields = "__all__"
```

Prefer:

```python
fields = ["title", "description", "date", "location", "capacity"]
```

When assigning automatic fields such as current user, use:

```python
form.save(commit=False)
```

Example:

```python
def form_valid(self, form):
    form.instance.organizer = self.request.user
    messages.success(self.request, "Event created successfully.")
    return super().form_valid(form)
```

Use `cleaned_data` for validated data when writing custom form logic.

If `django-crispy-forms` is used, configure Bootstrap 5 properly and render forms consistently.

---

# 11. Templates and UI

## Template inheritance

Use template inheritance.

Recommended structure:

```txt
base.html
events/base_events.html
events/event_list.html
events/event_detail.html
events/event_form.html
events/event_confirm_delete.html
```

A three-level template hierarchy is allowed if it improves maintainability, but it is not mandatory for every page.

## Template rules

Use Django Template Language.

Use:

- `{% extends %}`;
- `{% block %}`;
- `{% include %}`;
- `{% url %}`;
- `{% if %}`;
- `{% for %}`;
- `{% csrf_token %}`.

Avoid complex business logic in templates.

Move complex logic to:

- model properties;
- view context;
- custom template filters/tags only if genuinely useful.

## User feedback

Use Django messages for important actions:

- successful creation;
- successful update;
- successful deletion;
- registration completed;
- registration cancelled;
- permission denied;
- invalid action.

The user should always understand what happened.

---

# 12. Security Rules

The project must avoid common web security mistakes.

## Required

- use Django ORM instead of raw SQL unless there is a very specific reason;
- use Django Forms / ModelForms for validation;
- include CSRF token in all POST forms;
- do not disable CSRF middleware;
- avoid marking user-generated content as safe;
- do not store secrets in GitHub;
- use environment variables for production secrets;
- set `DEBUG = False` in production;
- configure `ALLOWED_HOSTS`;
- configure `CSRF_TRUSTED_ORIGINS` when required by deployment.

## Production settings

In production:

```python
DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = [...]
CSRF_TRUSTED_ORIGINS = [...]
```

Never commit real secrets.

---

# 13. Docker and Reproducibility

Docker is recommended for reproducibility, but the academic priority is a working repository, populated SQLite database, deployment, and clear README.

Use Docker only if it does not slow down completion of the Full-Stack app.

## If Docker is used

Include:

```txt
Dockerfile
.dockerignore
docker-compose.yml
Makefile
```

Dockerfile best practices:

- use a specific base image tag, for example `python:3.12-slim`;
- do not use `latest`;
- use `.dockerignore`;
- avoid unnecessary packages;
- use a non-root user;
- use exec-form `CMD`;
- do not store secrets inside the image;
- use environment variables for configuration.

Example CMD style:

```dockerfile
CMD ["gunicorn", "django_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Docker Compose

If `docker-compose.yml` is used:

- do not use the deprecated `version` key;
- define services clearly;
- use volumes only where useful;
- document every command in README;
- avoid unnecessary multi-container complexity if SQLite is used.

## Makefile

A `Makefile` is useful for repeatable commands.

Recommended targets:

```makefile
install
run
migrate
makemigrations
createsuperuser
test
seed
collectstatic
docker-build
docker-up
docker-down
```

Do not add Makefile targets that do not work.

---

# 14. Deployment

The project must be deployed online.

Allowed platforms include:

- Railway;
- Render;
- PythonAnywhere;
- Heroku;
- Vercel, if appropriate;
- equivalent free/free-plan service.

## Railway notes

If using Railway, include deployment-related instructions only if actually used.

Potentially useful files:

```txt
Procfile
runtime.txt
requirements.txt
```

Example `Procfile`:

```txt
web: gunicorn django_project.wsgi:application
```

If a production superuser is created via Railway CLI, document it in README:

```bash
railway run python manage.py createsuperuser
```

---

# 15. Optional REST API Stretch Goal

REST API endpoints are optional.

Add them only after the Full-Stack browser workflow is complete.

If implemented, use Django REST Framework.

Required files:

```txt
serializers.py
api_views.py or views.py
api_urls.py or urls.py
```

Recommended API prefix:

```txt
/api/
```

Use serializers to convert model instances/querysets to JSON and validate incoming data.

Useful DRF generic views:

- `ListAPIView`;
- `ListCreateAPIView`;
- `RetrieveAPIView`;
- `RetrieveUpdateDestroyAPIView`.

Use DRF permissions if endpoints are writable:

- `AllowAny`;
- `IsAuthenticated`;
- `IsAdminUser`;
- `IsAuthenticatedOrReadOnly`;
- custom permissions only when necessary.

Do not add CORS unless there is a separate JavaScript frontend on another origin.

---

# 16. README.md Required Structure

The README must allow the instructor to test the project immediately.

Required sections:

## 1. Project title and students

Include project name and student names.

## 2. Project type and framework

Example:

```txt
Project type: Full-Stack Web Application
Framework: Django
```

## 3. Description

Short explanation of the app and its purpose.

## 4. Features by role

Example:

```txt
Anonymous user:
- view public event list
- view event detail

Attendee:
- login/logout
- register for events
- cancel own registrations
- view own registrations

Organizer:
- create events
- update/delete own events
- view attendees for own events

Admin:
- manage data through Django Admin
```

## 5. Local installation

Include commands:

```bash
git clone ...
cd ...
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

If using Makefile, include equivalent commands:

```bash
make install
make migrate
make run
```

## 6. SQLite database

State clearly:

```txt
The repository includes db.sqlite3 with demo data and demo accounts.
```

## 7. Demo accounts

Include username, password, and role.

Example:

```txt
admin_demo / admin12345 — Admin
attendee_demo / attendee12345 — Attendee
organizer_demo / organizer12345 — Organizer
```

## 8. Deployment link

Add the deployed URL.

## 9. Browser-based testing scenario

Write a short step-by-step test.

Example:

```txt
1. Open the deployment link.
2. Log in as attendee_demo.
3. Open the event list.
4. Register for an event.
5. Open "My registrations" and verify the registration appears.
6. Log out.
7. Log in as organizer_demo.
8. Create a new event.
9. Edit the event.
10. Open the attendee list for one of your events.
11. Try to edit an event owned by another organizer and verify that access is denied.
```

## 10. Optional API documentation

Only include this section if REST endpoints are implemented.

For each endpoint, document:

- method;
- URL;
- authentication requirement;
- allowed role;
- request body;
- response example;
- short description.

---

# 17. Definition of Done

The project is complete only when all these checks pass.

## Functional checks

- app runs locally;
- app is deployed online;
- login/logout works;
- demo accounts work;
- every role has at least one meaningful workflow;
- main resource has CRUD;
- permissions are enforced server-side;
- unauthorized actions are blocked;
- database contains realistic demo data;
- README testing scenario works exactly as written.

## Code checks

- no virtual environment committed;
- migrations are present and coherent;
- `requirements.txt` is complete;
- no unused major files;
- no hardcoded URLs;
- no hardcoded secrets;
- forms validate input;
- templates use inheritance;
- views are readable and modular;
- code is not over-commented, but non-obvious business rules are explained.

## Deployment checks

- deployment link works;
- `DEBUG = False` in production;
- static files load correctly;
- demo workflow works on deployed version;
- README reflects the real deployment setup.

---

# 18. Instructions for AI Coding Agents

When generating or modifying code:

1. Prioritize academic compliance over unnecessary complexity.
2. Implement the Full-Stack browser workflow first.
3. Do not switch to REST API architecture unless explicitly requested.
4. Keep Django apps modular.
5. Use Django built-in auth, forms, ORM, templates, messages, and permissions.
6. Do not hardcode URLs.
7. Do not use raw SQL unless explicitly justified.
8. Do not create fake UI elements that are not backed by database logic.
9. Do not hide permission problems only in templates; enforce them in views/querysets.
10. Keep the custom user model minimal.
11. Add Docker only if it remains maintainable and documented.
12. Keep README synchronized with the actual code.
13. Before considering the task complete, test the exact README scenario from a clean clone.

---

# 19. Useful Links

## Course / submission

- Submission form: https://forms.gle/SJE19bFLXxMTVd2EA

## Django

- Django documentation: https://docs.djangoproject.com/
- Django Class-Based Views reference: https://ccbv.co.uk/
- Django design philosophies: https://docs.djangoproject.com/en/5.2/misc/design-philosophies/

## Docker

- Docker guides: https://docs.docker.com/guides/
- Course Docker repository: https://github.com/mbertini/tutorial-docker

## Optional DRF

- Django REST Framework documentation: https://www.django-rest-framework.org/
