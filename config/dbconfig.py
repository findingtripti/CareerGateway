"""Database settings from a DATABASE_URL (PDF section 16: PostgreSQL).

Without DATABASE_URL the project uses the local SQLite file, so development
needs no setup. On a host, set DATABASE_URL to the PostgreSQL address it
gives you, for example postgres://user:password@host:5432/dbname.
Standard library only.
"""

from urllib.parse import parse_qsl, unquote, urlparse

POSTGRES_SCHEMES = ("postgres", "postgresql")


def database_from_url(url, base_dir):
    url = (url or "").strip()
    if not url:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": base_dir / "db.sqlite3",
        }
    parsed = urlparse(url)
    if parsed.scheme not in POSTGRES_SCHEMES:
        # Never echo the URL: it contains the password.
        raise ValueError("DATABASE_URL must start with postgres:// or postgresql://")
    config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or ""),
        "CONN_MAX_AGE": 60,
    }
    options = dict(parse_qsl(parsed.query))
    if options:
        config["OPTIONS"] = options
    return config
