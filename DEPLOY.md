# Deploying Career Gateway

The project is ready for a Python host with PostgreSQL. Exact button names differ by host and free-tier
rules change, so check your host's current documentation. Free hosts may sleep when idle, and some free
databases expire.

## What the code already supports

- `DATABASE_URL=postgres://user:password@host:5432/dbname` switches from SQLite to PostgreSQL.
- `gunicorn` serves the app, `whitenoise` serves static files, `psycopg` talks to PostgreSQL (all in `requirements.txt`).
- `DJANGO_SECURE_DEPLOY=True` turns on https redirect, secure cookies and HSTS.
- All secrets come from environment variables. `.env` is never uploaded.

## Environment variables to set on the host

| Name | Value |
|---|---|
| DJANGO_SECRET_KEY | a new long random value (do not reuse your local one) |
| DJANGO_DEBUG | False |
| DJANGO_ALLOWED_HOSTS | your site's host name, e.g. myapp.onrender.com |
| DJANGO_CSRF_TRUSTED_ORIGINS | https://your-site-host-name |
| DJANGO_SECURE_DEPLOY | True |
| DATABASE_URL | the PostgreSQL address the host gives you |
| LLM_PROVIDER | gemini (or none) |
| GEMINI_API_KEY | your free key (paste it only into the host's secret settings) |
| GEMINI_MODEL / GEMINI_FALLBACK_MODEL | e.g. gemini-3.5-flash-lite / gemini-3.1-flash-lite |
| GEMINI_EMBEDDING_MODEL | gemini-embedding-001 (optional; this is the default) |

Ollama needs a computer you control, so on a normal free host use Gemini or `none`.

## Commands

Build command:
```
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```
Start command:
```
gunicorn config.wsgi
```
After the first deploy, open the host's shell (or run once locally with the production DATABASE_URL) and run:
```
python manage.py seed_careers
python manage.py seed_knowledge
python manage.py seed_demo_colleges
python manage.py seed_demo_opportunities
python manage.py seed_demo_mentors
python manage.py seed_demo_school_programs
# Needs GEMINI_API_KEY. Safe to re-run; resumes where it stopped.
python manage.py build_embeddings
python manage.py createsuperuser
```

## Check list after deploy

1. Open the site over https and click through Home, Careers, Colleges, Ask.
2. Ask "what is an entrance exam": you should see an AI-written answer with sources.
3. Log in to /admin/ and the staff dashboards.
4. Confirm the demo banners ("fictional demo") are visible.
5. Rotate the Gemini key if it was ever pasted anywhere public.

## Before real students use it

Replace the fictional demo data with real, verified records, review the knowledge entries, get consent for
real mentors, and review the privacy notice for minors.
