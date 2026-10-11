from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import StudentProfile


class PublicPageTests(TestCase):
    """Pages anyone can open without logging in."""

    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_careers_page_loads_for_anonymous_user(self):
        response = self.client.get(reverse("careers"))
        self.assertEqual(response.status_code, 200)

    def test_login_and_signup_pages_load(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("signup")).status_code, 200)


class SignupTests(TestCase):
    def test_signup_creates_user_and_redirects_to_login(self):
        response = self.client.post(reverse("signup"), {
            "username": "newstudent",
            "password": "StrongPass#123",
            "confirm_password": "StrongPass#123",
        })
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="newstudent").exists())

    def test_signup_rejects_password_mismatch(self):
        self.client.post(reverse("signup"), {
            "username": "newstudent",
            "password": "StrongPass#123",
            "confirm_password": "different",
        })
        self.assertFalse(User.objects.filter(username="newstudent").exists())

    def test_signup_rejects_duplicate_username(self):
        User.objects.create_user("taken", password="StrongPass#123")
        self.client.post(reverse("signup"), {
            "username": "taken",
            "password": "StrongPass#123",
            "confirm_password": "StrongPass#123",
        })
        self.assertEqual(User.objects.filter(username="taken").count(), 1)

    def test_signup_rejects_empty_fields(self):
        self.client.post(reverse("signup"), {
            "username": "",
            "password": "",
            "confirm_password": "",
        })
        self.assertEqual(User.objects.count(), 0)

class SignupPasswordRuleTests(TestCase):
    """Django's password validators must be enforced at signup."""

    def signup(self, username, password):
        return self.client.post(reverse("signup"), {
            "username": username,
            "password": password,
            "confirm_password": password,
        })

    def test_rejects_too_short_password(self):
        self.signup("shortpw", "ab1#x")
        self.assertFalse(User.objects.filter(username="shortpw").exists())

    def test_rejects_common_password(self):
        self.signup("commonpw", "password123")
        self.assertFalse(User.objects.filter(username="commonpw").exists())

    def test_rejects_numeric_only_password(self):
        self.signup("numericpw", "84739201847")
        self.assertFalse(User.objects.filter(username="numericpw").exists())

    def test_rejects_password_similar_to_username(self):
        self.signup("ashaverma", "ashaverma1")
        self.assertFalse(User.objects.filter(username="ashaverma").exists())

    def test_weak_password_shows_error_message(self):
        response = self.signup("shortpw", "ab1#x")
        self.assertContains(response, "too short")


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "student1", password="StrongPass#123"
        )

    def test_login_with_correct_password(self):
        response = self.client.post(reverse("login"), {
            "username": "student1",
            "password": "StrongPass#123",
        })
        self.assertRedirects(response, reverse("home"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_with_wrong_password_fails(self):
        response = self.client.post(reverse("login"), {
            "username": "student1",
            "password": "wrong",
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_with_post_ends_session(self):
        self.client.login(username="student1", password="StrongPass#123")
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_with_get_does_not_log_out(self):
        self.client.login(username="student1", password="StrongPass#123")
        self.client.get(reverse("logout"))
        self.assertIn("_auth_user_id", self.client.session)

class LoginRedirectTests(TestCase):
    """After login, students return to the page they originally wanted."""

    def setUp(self):
        User.objects.create_user("student1", password="StrongPass#123")
        self.credentials = {
            "username": "student1",
            "password": "StrongPass#123",
        }

    def login_url_with_next(self, next_value):
        return reverse("login") + "?next=" + next_value

    def test_protected_page_sends_visitor_to_login_with_next(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(
            response.url,
            reverse("login") + "?next=" + reverse("profile"),
        )

    def test_login_redirects_to_requested_page(self):
        response = self.client.post(
            self.login_url_with_next(reverse("profile")), self.credentials
        )
        self.assertRedirects(response, reverse("profile"))

    def test_login_without_next_goes_home(self):
        response = self.client.post(reverse("login"), self.credentials)
        self.assertRedirects(response, reverse("home"))

    def test_login_ignores_external_next_url(self):
        response = self.client.post(
            self.login_url_with_next("https://evil.example.com/"),
            self.credentials,
        )
        self.assertRedirects(response, reverse("home"))

    def test_login_ignores_protocol_relative_next_url(self):
        response = self.client.post(
            self.login_url_with_next("//evil.example.com"),
            self.credentials,
        )
        self.assertRedirects(response, reverse("home"))


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "student1", password="StrongPass#123"
        )
        self.other = User.objects.create_user(
            "student2", password="StrongPass#123"
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_profile_saves_valid_data(self):
        self.client.login(username="student1", password="StrongPass#123")
        response = self.client.post(reverse("profile"), {
            "full_name": "Asha Verma",
            "age": "17",
            "budget": "250000",
            "preferred_location": "Delhi",
        })
        self.assertRedirects(response, reverse("profile"))
        profile = StudentProfile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, "Asha Verma")
        self.assertEqual(profile.age, 17)
        self.assertEqual(profile.preferred_location, "Delhi")

    def test_profile_rejects_invalid_age(self):
        self.client.login(username="student1", password="StrongPass#123")
        self.client.post(reverse("profile"), {"age": "abc"})
        profile = StudentProfile.objects.get(user=self.user)
        self.assertIsNone(profile.age)

    def test_profile_rejects_negative_budget(self):
        self.client.login(username="student1", password="StrongPass#123")
        self.client.post(reverse("profile"), {"budget": "-5"})
        profile = StudentProfile.objects.get(user=self.user)
        self.assertIsNone(profile.budget)

    def test_student_cannot_see_another_students_profile(self):
        StudentProfile.objects.create(
            user=self.other, full_name="Secret Other Student"
        )
        self.client.login(username="student1", password="StrongPass#123")
        response = self.client.get(reverse("profile"))
        self.assertNotContains(response, "Secret Other Student")
class ProfileClearAndValidationTests(TestCase):
    """Students must be able to remove saved details; bad input saves nothing."""

    def setUp(self):
        self.user = User.objects.create_user(
            "student1", password="StrongPass#123"
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            full_name="Asha Verma",
            age=17,
            skills="python",
            budget=250000,
            preferred_location="Delhi",
        )
        self.client.login(username="student1", password="StrongPass#123")

    def reload(self):
        return StudentProfile.objects.get(user=self.user)

    def test_empty_text_value_clears_field(self):
        self.client.post(reverse("profile"), {"skills": ""})
        self.assertEqual(self.reload().skills, "")

    def test_empty_age_clears_age(self):
        self.client.post(reverse("profile"), {"age": ""})
        self.assertIsNone(self.reload().age)

    def test_empty_budget_clears_budget(self):
        self.client.post(reverse("profile"), {"budget": ""})
        self.assertIsNone(self.reload().budget)

    def test_field_missing_from_request_is_left_unchanged(self):
        self.client.post(reverse("profile"), {"skills": "design"})
        profile = self.reload()
        self.assertEqual(profile.skills, "design")
        self.assertEqual(profile.full_name, "Asha Verma")
        self.assertEqual(profile.age, 17)

    def test_infinite_budget_is_rejected(self):
        self.client.post(reverse("profile"), {"budget": "Infinity"})
        self.assertEqual(self.reload().budget, 250000)

    def test_too_large_budget_is_rejected(self):
        self.client.post(reverse("profile"), {"budget": "99999999999999"})
        self.assertEqual(self.reload().budget, 250000)

    def test_failed_validation_saves_nothing(self):
        self.client.post(reverse("profile"), {
            "full_name": "Changed Name",
            "age": "abc",
        })
        profile = self.reload()
        self.assertEqual(profile.full_name, "Asha Verma")
        self.assertEqual(profile.age, 17)

class AssistantTests(TestCase):
    def setUp(self):
        User.objects.create_user("student1", password="StrongPass#123")

    def test_assistant_requires_login(self):
        response = self.client.get(reverse("assistant"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_assistant_loads_for_logged_in_user(self):
        self.client.login(username="student1", password="StrongPass#123")
        response = self.client.get(reverse("assistant"))
        self.assertEqual(response.status_code, 200)

    def test_assistant_returns_three_recommendations(self):
        self.client.login(username="student1", password="StrongPass#123")
        response = self.client.post(reverse("assistant"), {
            "interest": "I like python programming and coding",
            "priority": "problem_solving",
        })
        self.assertEqual(response.status_code, 200)
        recommendations = response.context["recommendations"]
        self.assertEqual(len(recommendations), 3)
        self.assertEqual(recommendations[0]["title"], "Software Development")