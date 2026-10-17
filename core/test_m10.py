"""Final-bundle tests: Gemini retry and fallback model, deploy settings
helper, architecture page, home menu button, dashboard grammar."""

import os
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from config.dbconfig import database_from_url
from . import llm
from .models import KnowledgeEntry, SchoolProgram, SchoolRegistration
from .retrieval import retrieve

GEMINI = {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "k-123", "GEMINI_MODEL": "main-model",
          "GEMINI_FALLBACK_MODEL": "backup-model"}
OK = {"candidates": [{"content": {"parts": [{"text": "A written answer [1]."}]}}]}


def env(**extra):
    base = dict(GEMINI)
    base.update(extra)
    return mock.patch.dict(os.environ, base, clear=False)


class RetryAndFallbackTests(TestCase):
    def setUp(self):
        cache.clear()
        KnowledgeEntry.objects.create(
            title="What is an entrance exam?", entry_type="entrance_exam",
            content="An entrance exam decides admission.", keywords="entrance exam",
            is_published=True,
        )
        self.results = retrieve("entrance exam")
        self.sleep = mock.patch("core.llm._sleep").start()
        self.addCleanup(mock.patch.stopall)

    def run_llm(self, side_effect):
        with env(), mock.patch("core.llm._post_json", side_effect=side_effect) as post:
            out = llm.generate_answer("entrance exam", self.results, use_cache=False)
        return out, post

    def test_retries_after_503_then_succeeds(self):
        out, post = self.run_llm([llm.LLMError("503", retryable=True), OK])
        self.assertEqual(out["text"], "A written answer [1].")
        self.assertEqual(post.call_count, 2)
        self.assertEqual(out["model"], "main-model")

    def test_does_not_retry_bad_key(self):
        out, post = self.run_llm(llm.LLMError("403", retryable=False))
        self.assertIsNone(out)
        self.assertEqual(post.call_count, 1)

    def test_falls_back_to_second_model(self):
        busy = llm.LLMError("503", retryable=True)
        out, post = self.run_llm([busy, busy, busy, OK])
        self.assertEqual(out["model"], "backup-model")
        self.assertIn("backup-model", post.call_args_list[-1][0][0])

    def test_gives_up_when_everything_fails(self):
        busy = llm.LLMError("503", retryable=True)
        out, post = self.run_llm(busy)
        self.assertIsNone(out)
        self.assertEqual(post.call_count, 2 * llm.MAX_ATTEMPTS_PER_MODEL)

    def test_no_fallback_configured_means_one_model_only(self):
        busy = llm.LLMError("503", retryable=True)
        with env(GEMINI_FALLBACK_MODEL=""), mock.patch("core.llm._post_json", side_effect=busy) as post:
            out = llm.generate_answer("entrance exam", self.results, use_cache=False)
        self.assertIsNone(out)
        self.assertEqual(post.call_count, llm.MAX_ATTEMPTS_PER_MODEL)

    def test_waits_between_retries(self):
        self.run_llm([llm.LLMError("503", retryable=True), OK])
        self.sleep.assert_called()

    def test_http_503_and_429_are_retryable_but_400_is_not(self):
        import io
        import urllib.error
        for code, expected in ((503, True), (429, True), (400, False), (403, False)):
            err = urllib.error.HTTPError("u", code, "x", {}, io.BytesIO(b""))
            with mock.patch("urllib.request.urlopen", side_effect=err):
                with self.assertRaises(llm.LLMError) as cm:
                    llm._post_json("https://example.com", {}, {})
            self.assertEqual(cm.exception.retryable, expected, code)


class DatabaseConfigTests(TestCase):
    def test_default_is_sqlite(self):
        cfg = database_from_url("", Path("/app"))
        self.assertEqual(cfg["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(Path(cfg["NAME"]), Path("/app/db.sqlite3"))

    def test_postgres_url_is_parsed(self):
        cfg = database_from_url("postgres://user:p%40ss@db.example.com:5433/careers?sslmode=require", Path("/app"))
        self.assertEqual(cfg["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(cfg["NAME"], "careers")
        self.assertEqual(cfg["USER"], "user")
        self.assertEqual(cfg["PASSWORD"], "p@ss")
        self.assertEqual(cfg["HOST"], "db.example.com")
        self.assertEqual(cfg["PORT"], "5433")
        self.assertEqual(cfg["OPTIONS"], {"sslmode": "require"})

    def test_postgresql_scheme_also_works(self):
        self.assertEqual(
            database_from_url("postgresql://u:p@h/db", Path("/a"))["ENGINE"],
            "django.db.backends.postgresql",
        )

    def test_unknown_scheme_is_rejected(self):
        with self.assertRaises(ValueError):
            database_from_url("mysql://u:p@h/db", Path("/a"))

    def test_error_message_does_not_leak_password(self):
        with self.assertRaises(ValueError) as cm:
            database_from_url("mysql://u:secretpw@h/db", Path("/a"))
        self.assertNotIn("secretpw", str(cm.exception))


class ArchitecturePageTests(TestCase):
    def test_page_is_public_and_shows_the_flow(self):
        r = self.client.get(reverse("architecture"))
        self.assertEqual(r.status_code, 200)
        for word in ("Student", "Career Assistant", "Human Counsellor", "Professional Mentor",
                     "Opportunity", "Recommendation"):
            self.assertContains(r, word)

    def test_page_is_honest_about_limits(self):
        r = self.client.get(reverse("architecture"))
        self.assertContains(r, "not replace")
        self.assertContains(r, "embeddings")
        self.assertContains(r, "does not")

    def test_footer_links_to_architecture_page(self):
        self.assertContains(self.client.get(reverse("ask")), reverse("architecture"))


class SmallFixTests(TestCase):
    def test_home_has_mobile_menu_button(self):
        self.assertContains(self.client.get(reverse("home")), 'id="nav-toggle"')

    def test_dashboard_singular_grammar(self):
        staff = User.objects.create_user("st", "s@example.com", "pw12345678!", is_staff=True)
        kid = User.objects.create_user("k1", "k@example.com", "pw12345678!")
        prog = SchoolProgram.objects.create(
            title="P", event_date=date.today() + timedelta(days=5), is_published=True)
        SchoolRegistration.objects.create(
            user=kid, program=prog, school_name="S", consent_given=True)
        self.client.login(username="st", password="pw12345678!")
        r = self.client.get(reverse("school_dashboard"))
        self.assertContains(r, "</strong> registration,")
        self.assertNotContains(r, "</strong> registrations,")


class DocsExistTests(TestCase):
    root = Path(__file__).resolve().parent.parent

    def test_docs_exist(self):
        for name in ("README.md", "DEPLOY.md"):
            self.assertTrue((self.root / name).exists(), name)

    def test_docs_state_the_honest_limits(self):
        text = (self.root / "README.md").read_text(encoding="utf-8").lower()
        for phrase in ("embeddings", "fictional", "not verified", "booking"):
            self.assertIn(phrase, text)

    def test_requirements_are_utf8_and_list_deploy_packages(self):
        raw = (self.root / "requirements.txt").read_bytes()
        self.assertFalse(raw.startswith(b"\xff\xfe"))
        text = raw.decode("utf-8").lower()
        for pkg in ("django", "gunicorn", "whitenoise", "psycopg"):
            self.assertIn(pkg, text)


class FooterOnOlderPagesTests(TestCase):
    """Home, careers, assistant and profile have their own templates, so the
    footer link must be present on them too."""

    def test_public_older_pages_have_footer_link(self):
        for name in ("home", "careers"):
            self.assertContains(self.client.get(reverse(name)), reverse("architecture"), msg_prefix=name)

    def test_logged_in_older_pages_have_footer_link(self):
        User.objects.create_user("ft", "f@example.com", "pw12345678!")
        self.client.login(username="ft", password="pw12345678!")
        for name in ("assistant", "profile"):
            self.assertContains(self.client.get(reverse(name)), reverse("architecture"), msg_prefix=name)

    def test_opportunities_page_has_footer_link(self):
        self.assertContains(self.client.get(reverse("opportunities")), reverse("architecture"))
