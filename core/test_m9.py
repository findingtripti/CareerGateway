"""Milestone 9 tests: school version (PDF section 11) with minor-privacy
safeguards, chat widget interaction fixes, and retrieval ranking."""

from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import (
    College, Course, KnowledgeEntry, SchoolProgram, SchoolRegistration,
)
from .retrieval import retrieve


def make_program(**kw):
    defaults = dict(
        title="Career Awareness Workshop",
        program_type="workshop",
        description="A fictional workshop for demonstration.",
        event_date=date.today() + timedelta(days=20),
        location="Demo School Hall",
        is_published=True,
        is_demo=True,
    )
    defaults.update(kw)
    return SchoolProgram.objects.create(**defaults)


class SchoolPageTests(TestCase):
    def test_school_page_is_public_and_lists_published_programs(self):
        make_program(title="Visible Workshop")
        make_program(title="Hidden Workshop", is_published=False)
        r = self.client.get(reverse("school"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Visible Workshop")
        self.assertNotContains(r, "Hidden Workshop")

    def test_school_page_links_existing_tools_and_is_honest(self):
        r = self.client.get(reverse("school"))
        for name in ("assistant", "careers", "counsellor_request", "mentors", "opportunities"):
            self.assertContains(r, reverse(name))
        self.assertContains(r, "does not book")

    def test_demo_program_is_labelled(self):
        make_program()
        self.assertContains(self.client.get(reverse("school")), "fictional")

    def test_navbar_has_school_link(self):
        self.assertContains(self.client.get(reverse("school")), 'href="%s"' % reverse("school"))


class SchoolRegistrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("stu", "s@example.com", "pw12345678!")
        self.program = make_program()
        self.url = reverse("school_register", args=[self.program.pk])

    def post(self, **extra):
        data = {"school_name": "Demo Public School", "consent": "1"}
        data.update(extra)
        return self.client.post(self.url, data)

    def test_requires_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r["Location"])

    def test_adult_registration_saved(self):
        self.client.login(username="stu", password="pw12345678!")
        r = self.post()
        self.assertEqual(r.status_code, 302)
        reg = SchoolRegistration.objects.get()
        self.assertEqual(reg.user, self.user)
        self.assertFalse(reg.is_under_18)

    def test_consent_required(self):
        self.client.login(username="stu", password="pw12345678!")
        self.post(consent="")
        self.assertEqual(SchoolRegistration.objects.count(), 0)

    def test_school_name_required(self):
        self.client.login(username="stu", password="pw12345678!")
        self.post(school_name="  ")
        self.assertEqual(SchoolRegistration.objects.count(), 0)

    def test_minor_needs_guardian_consent(self):
        self.client.login(username="stu", password="pw12345678!")
        r = self.post(is_under_18="1")
        self.assertEqual(SchoolRegistration.objects.count(), 0)
        self.assertContains(r, "parent or guardian")

    def test_minor_with_guardian_consent_saved(self):
        self.client.login(username="stu", password="pw12345678!")
        self.post(is_under_18="1", guardian_consent="1")
        reg = SchoolRegistration.objects.get()
        self.assertTrue(reg.is_under_18)
        self.assertTrue(reg.guardian_consent)

    def test_no_phone_or_email_collected_for_registration(self):
        names = {f.name for f in SchoolRegistration._meta.get_fields()}
        for forbidden in ("contact_phone", "contact_email", "phone", "email", "address"):
            self.assertNotIn(forbidden, names)

    def test_duplicate_registration_not_created(self):
        self.client.login(username="stu", password="pw12345678!")
        self.post()
        self.post()
        self.assertEqual(SchoolRegistration.objects.count(), 1)

    def test_past_program_cannot_be_registered(self):
        past = make_program(title="Old", event_date=date.today() - timedelta(days=2))
        self.client.login(username="stu", password="pw12345678!")
        self.client.post(reverse("school_register", args=[past.pk]),
                         {"school_name": "X", "consent": "1"})
        self.assertEqual(SchoolRegistration.objects.count(), 0)

    def test_unpublished_program_is_404(self):
        hidden = make_program(title="Hid", is_published=False)
        self.client.login(username="stu", password="pw12345678!")
        r = self.client.get(reverse("school_register", args=[hidden.pk]))
        self.assertEqual(r.status_code, 404)

    def test_form_mentions_minor_safeguards(self):
        self.client.login(username="stu", password="pw12345678!")
        r = self.client.get(self.url)
        self.assertContains(r, "under 18")
        self.assertContains(r, "no phone number")

    def test_school_name_length_capped(self):
        self.client.login(username="stu", password="pw12345678!")
        self.post(school_name="A" * 500)
        self.assertLessEqual(len(SchoolRegistration.objects.get().school_name), 150)


class SchoolDashboardTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff", "t@example.com", "pw12345678!", is_staff=True)
        self.student = User.objects.create_user("kid", "k@example.com", "pw12345678!")
        self.program = make_program()
        SchoolRegistration.objects.create(
            user=self.student, program=self.program, school_name="Demo Public School",
            is_under_18=True, guardian_consent=True, consent_given=True,
        )

    def test_staff_only(self):
        url = reverse("school_dashboard")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.login(username="kid", password="pw12345678!")
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_staff_sees_aggregates_without_student_identity(self):
        self.client.login(username="staff", password="pw12345678!")
        r = self.client.get(reverse("school_dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Career Awareness Workshop")
        self.assertContains(r, "Demo Public School")
        self.assertNotContains(r, "kid")
        self.assertNotContains(r, "k@example.com")

    def test_dashboard_counts_minors(self):
        self.client.login(username="staff", password="pw12345678!")
        r = self.client.get(reverse("school_dashboard"))
        self.assertEqual(r.context["total_registrations"], 1)
        self.assertEqual(r.context["total_minors"], 1)

    def test_navbar_dashboard_link_staff_only(self):
        self.client.login(username="kid", password="pw12345678!")
        self.assertNotContains(self.client.get(reverse("home")), reverse("school_dashboard"))
        self.client.login(username="staff", password="pw12345678!")
        self.assertContains(self.client.get(reverse("home")), reverse("school_dashboard"))


class SchoolSeedAndAdminTests(TestCase):
    def test_seed_is_idempotent_and_fictional(self):
        call_command("seed_demo_school_programs")
        n = SchoolProgram.objects.count()
        self.assertGreaterEqual(n, 3)
        call_command("seed_demo_school_programs")
        self.assertEqual(SchoolProgram.objects.count(), n)
        self.assertTrue(all(p.is_demo for p in SchoolProgram.objects.all()))
        self.assertTrue(all(p.event_date >= date.today() for p in SchoolProgram.objects.all()))

    def test_admin_pages_open(self):
        User.objects.create_superuser("root", "r@example.com", "pw12345678!")
        self.client.login(username="root", password="pw12345678!")
        make_program()
        for name in ("schoolprogram", "schoolregistration"):
            self.assertEqual(self.client.get(reverse("admin:core_%s_changelist" % name)).status_code, 200)


class ChatWidgetInteractionTests(TestCase):
    def setUp(self):
        self.html = (Path(__file__).parent / "templates/core/_chat_widget.html").read_text(encoding="utf-8")

    def test_panel_comes_before_toggle_so_it_opens_above(self):
        self.assertLess(self.html.index('id="cg-chat-panel"'), self.html.index('id="cg-chat-toggle"'))

    def test_has_clear_button_and_you_asked(self):
        self.assertIn("cg-chat-clear", self.html)
        self.assertIn("You asked", self.html)

    def test_old_answer_cleared_when_typing(self):
        self.assertIn('addEventListener("input"', self.html)

    def test_guards_against_stale_responses(self):
        self.assertIn("requestId", self.html)

    def test_still_no_innerhtml(self):
        self.assertNotIn("innerHTML", self.html)

    def test_widget_rendered_on_pages(self):
        self.assertContains(self.client.get(reverse("home")), "cg-chat-clear")


class RetrievalRankingTests(TestCase):
    def setUp(self):
        College.objects.create(
            name="Riverbend Institute", location="Pune", is_published=True,
            description="A fictional college with hostels.",
        )
        KnowledgeEntry.objects.create(
            title="How to compare colleges", entry_type="admission_process",
            content="Compare fees, placements and eligibility.",
            keywords="compare, colleges", is_published=True,
        )

    def test_title_match_beats_generic_body_match(self):
        out = retrieve("compare college for me")
        self.assertEqual(out[0]["title"], "How to compare colleges")

    def test_generic_word_only_body_match_ranks_below_specific_match(self):
        out = retrieve("compare college")
        titles = [r["title"] for r in out]
        if "Riverbend Institute" in titles:
            self.assertGreater(titles.index("Riverbend Institute"), titles.index("How to compare colleges"))

    def test_generic_only_query_still_returns_results(self):
        self.assertTrue(retrieve("college"))

    def test_specific_body_word_beats_generic_body_word(self):
        KnowledgeEntry.objects.create(
            title="Aaa note", entry_type="faq", is_published=True,
            content="This note mentions a college once.",
        )
        KnowledgeEntry.objects.create(
            title="Zzz note", entry_type="faq", is_published=True,
            content="Tips to compare options carefully.",
        )
        titles = [r["title"] for r in retrieve("compare college")]
        self.assertLess(titles.index("Zzz note"), titles.index("Aaa note"))
