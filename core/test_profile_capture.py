"""Tests for gradual profile capture in the assistant (PDF section 4)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core import profile_capture as pc
from core.models import StudentProfile

User = get_user_model()


class CleanAnswerTests(TestCase):
    def test_blank_is_rejected(self):
        value, error = pc.clean_answer("full_name", "   ")
        self.assertIsNone(value)
        self.assertIn("Skip", error)

    def test_text_is_trimmed(self):
        self.assertEqual(pc.clean_answer("skills", "  Python  "),
                         ("Python", None))

    def test_text_too_long(self):
        value, error = pc.clean_answer("skills", "x" * 501)
        self.assertIsNone(value)
        self.assertIn("500", error)

    def test_age_valid_and_boundaries(self):
        self.assertEqual(pc.clean_answer("age", "1"), (1, None))
        self.assertEqual(pc.clean_answer("age", "120"), (120, None))

    def test_age_invalid(self):
        for bad in ("0", "121", "abc", "-5", "12.5"):
            value, error = pc.clean_answer("age", bad)
            self.assertIsNone(value, bad)
            self.assertIn("valid age", error)

    def test_budget_valid(self):
        self.assertEqual(pc.clean_answer("budget", "50000"),
                         (Decimal("50000"), None))
        self.assertEqual(pc.clean_answer("budget", "0"),
                         (Decimal("0"), None))

    def test_budget_invalid(self):
        for bad in ("abc", "-1", "NaN", "Infinity", "99999999999"):
            value, error = pc.clean_answer("budget", bad)
            self.assertIsNone(value, bad)
            self.assertTrue(error, bad)

    def test_unknown_field(self):
        value, error = pc.clean_answer("is_staff", "1")
        self.assertIsNone(value)
        self.assertTrue(error)


class QuestionOrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("asha", password="pw-12345-x")

    def test_first_question_for_empty_profile(self):
        profile = StudentProfile(user=self.user)
        self.assertEqual(pc.next_question(profile).key, "full_name")
        self.assertEqual(pc.progress(profile), (0, pc.TOTAL))

    def test_filled_fields_are_skipped_over(self):
        profile = StudentProfile(user=self.user, full_name="Asha", age=17)
        self.assertEqual(pc.next_question(profile).key, "current_education")
        self.assertEqual(pc.progress(profile), (2, pc.TOTAL))

    def test_skipped_fields_are_passed_over(self):
        profile = StudentProfile(user=self.user)
        self.assertEqual(pc.next_question(profile, ["full_name"]).key, "age")

    def test_complete_profile_has_no_question(self):
        profile = StudentProfile(
            user=self.user, full_name="A", age=18, current_education="x",
            preferred_location="x", budget=Decimal("0"),
            entrance_exams="x", subjects_and_interests="x", skills="x",
            career_interests="x", career_goals="x",
        )
        self.assertIsNone(pc.next_question(profile))

    def test_budget_zero_counts_as_answered(self):
        profile = StudentProfile(user=self.user, budget=Decimal("0"))
        self.assertTrue(pc.is_filled(profile, "budget"))

    def test_every_question_is_a_model_field(self):
        names = {f.name for f in StudentProfile._meta.get_fields()}
        for q in pc.QUESTIONS:
            self.assertIn(q.key, names)


class ProfileStepViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("asha", password="pw-12345-x")
        self.other = User.objects.create_user("ravi", password="pw-12345-x")
        self.url = reverse("profile_step")
        self.client.login(username="asha", password="pw-12345-x")

    def save(self, field, value, action="save"):
        return self.client.post(
            self.url, {"field": field, "value": value, "action": action}
        )

    def test_login_required(self):
        self.client.logout()
        response = self.save("full_name", "Asha")
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])
        self.assertFalse(StudentProfile.objects.exists())

    def test_get_is_not_allowed_and_saves_nothing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertFalse(StudentProfile.objects.exists())

    def test_save_text_answer(self):
        response = self.save("full_name", "  Asha Verma ")
        self.assertRedirects(
            response, reverse("assistant") + "#profile-step",
            fetch_redirect_response=False,
        )
        profile = StudentProfile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, "Asha Verma")

    def test_save_age_and_budget(self):
        self.save("age", "17")
        self.save("budget", "45000")
        profile = StudentProfile.objects.get(user=self.user)
        self.assertEqual(profile.age, 17)
        self.assertEqual(profile.budget, Decimal("45000"))

    def test_only_the_named_field_changes(self):
        StudentProfile.objects.create(
            user=self.user, full_name="Asha", skills="Python"
        )
        self.save("age", "17")
        profile = StudentProfile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, "Asha")
        self.assertEqual(profile.skills, "Python")
        self.assertEqual(profile.age, 17)

    def test_invalid_age_is_not_saved(self):
        response = self.save("age", "500")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(StudentProfile.objects.exists())
        follow = self.client.get(reverse("assistant"))
        self.assertContains(follow, "valid age between 1 and 120")

    def test_blank_does_not_clear_existing_value(self):
        StudentProfile.objects.create(user=self.user, full_name="Asha")
        self.save("full_name", "   ")
        self.assertEqual(
            StudentProfile.objects.get(user=self.user).full_name, "Asha"
        )

    def test_unknown_field_is_refused(self):
        self.save("is_staff", "1")
        self.save("user", "2")
        self.assertFalse(StudentProfile.objects.exists())
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)

    def test_cannot_change_another_users_profile(self):
        StudentProfile.objects.create(user=self.other, full_name="Ravi")
        self.save("full_name", "Hacked")
        self.assertEqual(
            StudentProfile.objects.get(user=self.other).full_name, "Ravi"
        )

    def test_skip_saves_nothing_and_moves_on(self):
        self.save("full_name", "", action="skip")
        self.assertFalse(StudentProfile.objects.exists())
        response = self.client.get(reverse("assistant"))
        self.assertContains(response, "How old are you?")
        self.assertNotContains(response, "What is your full name?")

    def test_skipped_question_can_be_asked_again(self):
        self.save("full_name", "", action="skip")
        self.client.post(self.url, {"action": "reset"})
        response = self.client.get(reverse("assistant"))
        self.assertContains(response, "What is your full name?")

    def test_answering_a_skipped_question_removes_the_skip(self):
        self.save("full_name", "", action="skip")
        self.save("full_name", "Asha")
        self.assertEqual(self.client.session.get(pc.SESSION_KEY), [])

    def test_redirect_never_follows_a_next_parameter(self):
        response = self.client.post(
            self.url,
            {"field": "full_name", "value": "Asha", "next": "https://evil.example"},
        )
        self.assertNotIn("evil", response["Location"])

    def test_junk_in_session_is_ignored(self):
        session = self.client.session
        session[pc.SESSION_KEY] = "not-a-list"
        session.save()
        response = self.client.get(reverse("assistant"))
        self.assertContains(response, "What is your full name?")


class CardDisplayTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("asha", password="pw-12345-x")

    def test_card_shows_on_assistant_for_logged_in_user(self):
        self.client.login(username="asha", password="pw-12345-x")
        response = self.client.get(reverse("assistant"))
        self.assertContains(response, "Complete your profile")
        self.assertContains(response, "0 of %d answered" % pc.TOTAL)
        self.assertContains(response, "Only what you type is saved")

    def test_viewing_the_page_does_not_create_a_profile(self):
        self.client.login(username="asha", password="pw-12345-x")
        self.client.get(reverse("assistant"))
        self.assertFalse(
            StudentProfile.objects.filter(user=self.user).exists()
        )

    def test_card_disappears_when_profile_is_complete(self):
        StudentProfile.objects.create(
            user=self.user, full_name="A", age=18, current_education="x",
            preferred_location="x", budget=Decimal("0"),
            entrance_exams="x", subjects_and_interests="x", skills="x",
            career_interests="x", career_goals="x",
        )
        self.client.login(username="asha", password="pw-12345-x")
        response = self.client.get(reverse("assistant"))
        self.assertNotContains(response, "Complete your profile")

    def test_progress_strip_on_profile_page(self):
        StudentProfile.objects.create(user=self.user, full_name="Asha")
        self.client.login(username="asha", password="pw-12345-x")
        response = self.client.get(reverse("profile"))
        self.assertContains(response, "Profile: 1 of %d answered" % pc.TOTAL)
        self.assertContains(response, "Answer a few quick questions")

    def test_no_card_text_for_anonymous_visitors(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "Complete your profile")
