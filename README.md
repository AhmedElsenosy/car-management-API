# Deploying Django to Railway (SQLite locally, PostgreSQL in production)

This project is a Django app configured to use:
- SQLite for local development (default)
- PostgreSQL on Railway via the `DATABASE_URL` environment variable

It already includes:
- requirements.txt (Django, djangorestframework, dj-database-url, psycopg2-binary, gunicorn, whitenoise)
- runtime.txt (Python version)
- Procfile (starts gunicorn bound to `$PORT` for Railway)
- settings.py reads `DATABASE_URL` when present, else falls back to SQLite

## 1) Local development (SQLite)

Prerequisites:
- Python 3.10.x (see `runtime.txt`)

Steps:
1. Create and activate a virtualenv (recommended)
   - python -m venv .venv
   - source .venv/bin/activate
2. Install dependencies
   - pip install -r requirements.txt
3. Apply migrations
   - python manage.py migrate
4. Run the server
   - python manage.py runserver

Optional (create superuser for admin):
- python manage.py createsuperuser

## 2) Prepare for Railway

Already in repo:
- Procfile: `web: gunicorn project.wsgi:application --bind 0.0.0.0:$PORT`
- runtime.txt: `python-3.10.12`
- settings.py: Uses `DATABASE_URL` if set, else SQLite. WhiteNoise is enabled for static files.

Ensure your app migrations exist and are committed (e.g., `python manage.py makemigrations` if you made model changes).

## 3) Deploy backend on Railway

A) Create a new project and deploy the service
1. Push your repo to GitHub (or GitLab/Bitbucket)
2. In Railway: New Project → Deploy from GitHub → select your repo/branch
3. Railway (Nixpacks) will detect Python from `requirements.txt` and use `runtime.txt`.
4. It will use the Procfile to start gunicorn on `$PORT`.

B) Provision PostgreSQL and attach it
1. In your Railway project: Add → Database → PostgreSQL
2. After creation, attach the database to your web service
3. Confirm your web service has the `DATABASE_URL` environment variable from the database

C) Configure environment variables (Service → Variables)
- SECRET_KEY: Generate a strong value (required for Django)
- DEBUG: `False` (for production)
- ALLOWED_HOSTS: Your Railway domain (e.g., `your-app.up.railway.app`) or `*` during initial testing

D) First-time setup commands (migrations and static files)
- After the first deploy, run these commands from the Railway UI (Service → Shell) or using the CLI:
  - python manage.py migrate
  - python manage.py collectstatic --noinput

E) Verify deployment
- Open your service URL to ensure it loads
- If using Django Admin, visit `/admin/` (create a superuser locally or via Railway shell)

## 4) Notes and best practices

- Database switching:
  - Local: No `DATABASE_URL` → SQLite (file `db.sqlite3`)
  - Railway: `DATABASE_URL` is injected automatically from the PostgreSQL plugin → dj-database-url parses it for Django

- Static files:
  - WhiteNoise is enabled via middleware
  - `collectstatic` will gather assets into `staticfiles/` for serving

- Security & hardening:
  - Set `DEBUG=False` in production
  - Prefer explicit `ALLOWED_HOSTS` (your exact Railway domain) over `*`
  - Keep `SECRET_KEY` secret (don’t commit it). Configure it as an env var in Railway.

- Logs & debugging:
  - Use Railway’s logs to monitor build/startup output
  - Common issues: missing migrations, incorrect `ALLOWED_HOSTS`, or failing `collectstatic`

## 5) Railway CLI (optional)

You can also manage the project via the Railway CLI:
- Install: https://docs.railway.app/cli/installation
- Login and link:
  - railway login
  - railway link
- Run admin commands against your service:
  - railway run python manage.py migrate
  - railway run python manage.py collectstatic --noinput

## 6) Troubleshooting
- App crashes on start:
  - Check that `SECRET_KEY` is set and `DEBUG=False`
  - Verify `ALLOWED_HOSTS` includes your Railway domain
- Database errors:
  - Ensure the PostgreSQL resource is attached and `DATABASE_URL` appears in service variables
  - Re-run `python manage.py migrate`
- Static files not loading:
  - Ensure `collectstatic` succeeded and WhiteNoise middleware is active

## 7) Project paths
This README assumes the Django project root (with manage.py) is at the same level as this file.
If your structure differs, adjust commands accordingly (e.g., add `--pythonpath` or run from the correct directory).
