from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from .career_matching import find_matches, rank_careers
from .college_matching import (
    StudentCriteria,
    detect_education_level,
    recommend_courses,
)
from .models import Career, CareerFAQ, College, Course, StudentProfile


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


class AuthPageAccessibilityTests(TestCase):
    """Login and signup share the site layout and have usable forms."""

    def test_login_page_has_labelled_fields_and_autocomplete(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, 'for="username"')
        self.assertContains(response, 'for="password"')
        self.assertContains(response, 'autocomplete="current-password"')

    def test_signup_page_has_labelled_fields_and_password_hint(self):
        response = self.client.get(reverse("signup"))
        self.assertContains(response, 'for="confirm_password"')
        self.assertContains(response, 'autocomplete="new-password"')
        self.assertContains(response, "at least 8 characters")

    def test_auth_pages_show_shared_navigation_for_visitors(self):
        for name in ("login", "signup"):
            response = self.client.get(reverse(name))
            self.assertContains(response, 'aria-label="Main navigation"')
            self.assertContains(response, reverse("careers"))
            self.assertNotContains(response, reverse("profile"))

    def test_error_message_is_styled_as_error(self):
        response = self.client.post(reverse("login"), {
            "username": "nobody",
            "password": "wrong",
        })
        self.assertContains(response, 'class="message error"')


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
        call_command("seed_careers", verbosity=0)
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


class AssistantStartingOptionsTests(TestCase):
    """PDF section 3: first conversation and the seven starting options."""

    OPTION_LABELS = [
        "Choosing a career",
        "Choosing a course",
        "Finding colleges",
        "Scholarships",
        "Talk to a professional",
        "Build my career roadmap",
        "I don't know what I want",
    ]

    def setUp(self):
        user = User.objects.create_user(
            "student1", password="StrongPass#123"
        )
        # A saved profile removes the page's own "profile is not available
        # yet" text, so "not available yet" below can only come from the
        # topic response.
        StudentProfile.objects.create(user=user, full_name="Asha Verma")
        self.client.login(username="student1", password="StrongPass#123")

    def get_assistant(self, topic=None):
        url = reverse("assistant")
        if topic:
            url += "?topic=" + topic
        return self.client.get(url)

    def test_welcome_text_from_pdf_is_shown(self):
        response = self.get_assistant()
        self.assertContains(response, "Welcome to Career Gateway")
        # Django escapes apostrophes (' becomes &#x27;), so compare escaped.
        self.assertContains(
            response,
            escape(
                "Let's understand where you want to go and explore the "
                "paths that can take you there."
            ),
        )

    def test_all_seven_starting_options_are_listed(self):
        response = self.get_assistant()
        for label in self.OPTION_LABELS:
            self.assertContains(response, escape(label))

    def test_not_sure_option_preselects_exploring_priority(self):
        response = self.get_assistant("unsure")
        self.assertEqual(response.context["priority"], "exploration")
        self.assertContains(response, "okay")

    def test_unbuilt_feature_is_honest_and_never_claims_booking(self):
        for topic in ("scholarships", "professional"):
            response = self.get_assistant(topic)
            self.assertContains(response, "not available yet")
            self.assertNotContains(response, "has been booked")
            self.assertNotContains(response, "assigned to you")

    def test_professional_option_uses_pdf_handoff_wording(self):
        response = self.get_assistant("professional")
        self.assertContains(
            response,
            "A career counsellor can help you evaluate them in more detail.",
        )

    def test_unknown_topic_is_ignored(self):
        response = self.get_assistant("<script>alert(1)</script>")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertEqual(response.context["topic"], "")

    def test_assistant_states_it_does_not_replace_a_counsellor(self):
        response = self.get_assistant()
        self.assertContains(response, "does not replace")
        self.assertContains(response, "professional career counsellor")


PDF_SECTION_6_HEADINGS = [
    "What professionals do",
    "Required education",
    "Entrance examinations",
    "Important skills",
    "Career pathway",
    "Possible roles",
    "Higher education options",
    "Work environments",
    "Professional insights",
    "Frequently asked questions",
]


class SeedCareersTests(TestCase):
    def test_seed_creates_careers_with_every_pdf_field_filled(self):
        call_command("seed_careers", verbosity=0)
        self.assertEqual(Career.objects.count(), 8)

        fields = [
            "summary", "what_professionals_do", "required_education",
            "entrance_exams", "important_skills", "career_pathway",
            "possible_roles", "higher_education_options",
            "work_environments", "professional_insights", "first_step",
            "keywords",
        ]
        for career in Career.objects.all():
            for field in fields:
                self.assertTrue(
                    getattr(career, field).strip(),
                    f"{career.title} has empty {field}",
                )
            self.assertGreaterEqual(career.faqs.count(), 2, career.title)

    def test_seed_is_safe_to_repeat_and_keeps_admin_edits(self):
        call_command("seed_careers", verbosity=0)
        career = Career.objects.get(slug="cybersecurity")
        career.summary = "Edited by staff."
        career.save()

        call_command("seed_careers", verbosity=0)

        self.assertEqual(Career.objects.count(), 8)
        career.refresh_from_db()
        self.assertEqual(career.summary, "Edited by staff.")
        self.assertEqual(career.faqs.count(), 2)

    def test_seeded_content_is_not_claimed_as_verified(self):
        call_command("seed_careers", verbosity=0)
        for career in Career.objects.all():
            self.assertEqual(
                career.verification_status, "needs_verification"
            )
            self.assertIsNone(career.last_reviewed)
            self.assertTrue(career.source_note)


class CareerMatchingTests(TestCase):
    def setUp(self):
        call_command("seed_careers", verbosity=0)

    def test_matching_uses_whole_words_only(self):
        self.assertEqual(find_matches(["ui"], "i enjoy building things"), [])
        self.assertEqual(find_matches(["ui"], "i like ui design"), ["ui"])

    def test_matching_handles_phrases(self):
        self.assertEqual(
            find_matches(["machine learning"], "interested in machine learning"),
            ["machine learning"],
        )

    def test_profile_words_raise_a_career_in_the_ranking(self):
        ranked, excluded = rank_careers(
            Career.objects.all(), interest_text="python programming coding"
        )
        self.assertEqual(ranked[0]["career"].slug, "software-development")
        self.assertEqual(excluded, [])
        self.assertIn("python", ranked[0]["answer_matches"])

    def test_less_coding_excludes_coding_heavy_careers(self):
        ranked, excluded = rank_careers(
            Career.objects.all(),
            interest_text="python programming coding",
            less_coding=True,
        )
        shown = [result["career"].slug for result in ranked]
        self.assertNotIn("software-development", shown)
        self.assertEqual(
            [career.slug for career in excluded], ["software-development"]
        )

    def test_priority_adds_to_the_score(self):
        ranked, _ = rank_careers(Career.objects.all(), priority="creativity")
        self.assertEqual(ranked[0]["career"].slug, "ui-ux-design")
        self.assertTrue(ranked[0]["priority_match"])


class CareerPagesTests(TestCase):
    def setUp(self):
        call_command("seed_careers", verbosity=0)

    def test_careers_page_lists_published_careers_from_database(self):
        response = self.client.get(reverse("careers"))
        self.assertEqual(len(response.context["careers"]), 8)
        self.assertContains(response, "Technology Consulting")

    def test_unpublished_career_is_hidden_everywhere(self):
        career = Career.objects.get(slug="cloud-computing")
        career.is_published = False
        career.save()

        listing = self.client.get(reverse("careers"))
        self.assertNotContains(listing, "Cloud Computing")

        detail = self.client.get(
            reverse("career_detail", args=["cloud-computing"])
        )
        self.assertEqual(detail.status_code, 404)

    def test_career_cards_keep_keys_used_by_the_compare_script(self):
        response = self.client.get(reverse("careers"))
        card = response.context["careers"][0]
        for key in ("title", "daily_work", "skills", "pathway",
                    "exams", "roles", "match_count", "match_reason"):
            self.assertIn(key, card)

    def test_careers_page_links_to_each_detail_page(self):
        response = self.client.get(reverse("careers"))
        self.assertContains(
            response, reverse("career_detail", args=["data-science"])
        )

    def test_profile_orders_careers_for_logged_in_student(self):
        user = User.objects.create_user("s1", password="StrongPass#123")
        StudentProfile.objects.create(
            user=user, skills="design, prototyping, creativity"
        )
        self.client.login(username="s1", password="StrongPass#123")
        response = self.client.get(reverse("careers"))
        self.assertEqual(response.context["careers"][0]["title"], "UI/UX Design")

    def test_detail_page_shows_all_pdf_section_6_headings(self):
        response = self.client.get(
            reverse("career_detail", args=["data-science"])
        )
        self.assertEqual(response.status_code, 200)
        for heading in PDF_SECTION_6_HEADINGS:
            self.assertContains(response, heading)

    def test_detail_page_shows_faqs_and_counsellor_next_step(self):
        response = self.client.get(
            reverse("career_detail", args=["data-science"])
        )
        self.assertContains(response, "Is data science only for people")
        self.assertContains(response, "Talk to a career counsellor")

    def test_detail_page_shows_data_quality_notice(self):
        response = self.client.get(
            reverse("career_detail", args=["data-science"])
        )
        self.assertContains(response, "Needs verification")
        self.assertContains(response, "Not reviewed yet")

    def test_unknown_career_returns_404(self):
        response = self.client.get(
            reverse("career_detail", args=["no-such-career"])
        )
        self.assertEqual(response.status_code, 404)

    def test_career_without_faqs_still_renders(self):
        Career.objects.get(slug="data-science").faqs.all().delete()
        response = self.client.get(
            reverse("career_detail", args=["data-science"])
        )
        self.assertEqual(response.status_code, 200)


class AssistantUsesCareerDatabaseTests(TestCase):
    def setUp(self):
        call_command("seed_careers", verbosity=0)
        User.objects.create_user("student1", password="StrongPass#123")
        self.client.login(username="student1", password="StrongPass#123")

    def post(self, **data):
        return self.client.post(reverse("assistant"), data)

    def test_recommendations_come_from_database_with_detail_links(self):
        response = self.post(interest="python programming coding")
        titles = [r["title"] for r in response.context["recommendations"]]
        self.assertEqual(titles[0], "Software Development")
        self.assertContains(
            response, reverse("career_detail", args=["software-development"])
        )

    def test_less_coding_choice_removes_coding_heavy_careers_and_says_why(self):
        response = self.post(
            interest="python programming coding", less_coding="1"
        )
        titles = [r["title"] for r in response.context["recommendations"]]
        self.assertNotIn("Software Development", titles)
        self.assertContains(response, "Not shown because you prefer less coding")
        self.assertContains(response, "Software Development")

    def test_unpublished_career_is_never_recommended(self):
        Career.objects.filter(slug="software-development").update(
            is_published=False
        )
        response = self.post(interest="python programming coding")
        titles = [r["title"] for r in response.context["recommendations"]]
        self.assertNotIn("Software Development", titles)

    def test_assistant_does_not_crash_when_no_careers_exist(self):
        Career.objects.all().delete()
        response = self.post(interest="coding")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["recommendations"], [])

    def test_whole_word_matching_in_assistant(self):
        response = self.post(interest="I enjoy building things")
        for result in response.context["recommendations"]:
            self.assertNotIn("ui", result["reason"].split(": ")[-1].split(", "))


class CareerAdminTests(TestCase):
    def test_career_is_manageable_in_admin(self):
        call_command("seed_careers", verbosity=0)
        User.objects.create_superuser("boss", "b@example.com", "StrongPass#123")
        self.client.login(username="boss", password="StrongPass#123")

        listing = self.client.get(reverse("admin:core_career_changelist"))
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, "Digital Forensics")

        career = Career.objects.get(slug="digital-forensics")
        edit = self.client.get(
            reverse("admin:core_career_change", args=[career.pk])
        )
        self.assertEqual(edit.status_code, 200)
        self.assertContains(edit, "Is digital forensics the same as")


def make_college(name="Test College", location="Delhi", verified=True,
                 partner=False, demo=False, last_verified=None,
                 published=True):
    return College.objects.create(
        name=name,
        location=location,
        is_verified=verified,
        is_published=published,
        is_demo=demo,
        last_verified=last_verified or date.today(),
        partner_status="partner" if partner else "none",
        partner_disclosure=(
            "Career Gateway has a commercial relationship with this college."
            if partner else ""
        ),
    )


def make_course(college, name="B.Tech Computer Science", fees=400000,
                min_education="class_12", careers=()):
    course = Course.objects.create(
        college=college, name=name, fees=fees, min_education=min_education
    )
    course.related_careers.set(careers)
    return course


def run(criteria, courses=None):
    if courses is None:
        courses = Course.objects.select_related("college")
    return recommend_courses(list(courses), criteria)


class EducationLevelDetectionTests(TestCase):
    def test_detects_levels_from_free_text(self):
        self.assertEqual(detect_education_level("Class 12 science"), "class_12")
        self.assertEqual(detect_education_level("12th grade"), "class_12")
        self.assertEqual(detect_education_level("Class 10"), "class_10")
        self.assertEqual(detect_education_level("B.Tech first year"), "graduate")
        self.assertEqual(detect_education_level("Bachelor of Arts"), "graduate")

    def test_unknown_text_gives_none(self):
        self.assertIsNone(detect_education_level(""))
        self.assertIsNone(detect_education_level("studying hard"))

    def test_does_not_match_inside_other_numbers(self):
        self.assertIsNone(detect_education_level("room 120"))


class CollegeMatchingRulesTests(TestCase):
    def setUp(self):
        self.college = make_college()

    def test_fees_above_budget_are_excluded_with_reason(self):
        make_course(self.college, fees=400000)
        out = run(StudentCriteria(budget=Decimal("100000")))
        self.assertEqual(out["results"], [])
        self.assertIn("budget", out["excluded"][0]["reason"].lower())

    def test_fees_within_budget_are_kept(self):
        make_course(self.college, fees=400000)
        out = run(StudentCriteria(budget=Decimal("500000")))
        self.assertEqual(len(out["results"]), 1)

    def test_unknown_fees_are_kept_but_flagged(self):
        make_course(self.college, fees=None)
        out = run(StudentCriteria(budget=Decimal("100000")))
        self.assertEqual(len(out["results"]), 1)
        self.assertTrue(
            any("fees" in note.lower() for note in out["results"][0]["unknowns"])
        )

    def test_education_below_requirement_is_excluded(self):
        make_course(self.college, min_education="graduate")
        out = run(StudentCriteria(education_level="class_12"))
        self.assertEqual(out["results"], [])
        self.assertIn("graduate", out["excluded"][0]["reason"].lower())

    def test_education_meeting_requirement_is_kept(self):
        make_course(self.college, min_education="class_12")
        out = run(StudentCriteria(education_level="class_12"))
        self.assertEqual(len(out["results"]), 1)

    def test_undetected_education_is_unknown_not_excluded(self):
        make_course(self.college, min_education="class_12")
        out = run(StudentCriteria(education_level=None))
        self.assertEqual(len(out["results"]), 1)
        self.assertTrue(out["results"][0]["unknowns"])

    def test_location_is_a_preference_that_reorders_but_never_excludes(self):
        far = make_college("Far College", location="Chennai")
        near = make_college("Near College", location="Pune")
        make_course(far)
        make_course(near)
        out = run(StudentCriteria(location="Pune"))
        names = [r["college"].name for r in out["results"]]
        self.assertEqual(names, ["Near College", "Far College"])

    def test_career_interest_is_a_preference(self):
        career = Career.objects.create(
            title="Cybersecurity", slug="cybersecurity", summary="s",
            what_professionals_do="a", required_education="a",
            entrance_exams="a", important_skills="a", career_pathway="a",
            possible_roles="a", higher_education_options="a",
            work_environments="a", professional_insights="a",
            keywords="security, networking",
        )
        plain = make_course(self.college, name="General Course")
        linked = make_course(self.college, name="Security Course",
                             careers=[career])
        out = run(StudentCriteria(interest_text="I enjoy security puzzles"))
        self.assertEqual(out["results"][0]["course"], linked)
        self.assertEqual(len(out["results"]), 2)
        self.assertIn(plain, [r["course"] for r in out["results"]])

    def test_partner_status_never_changes_the_order(self):
        make_college("A College", partner=False)
        make_college("B College", partner=True)
        for college in College.objects.all():
            make_course(college)
        before = [r["college"].name for r in run(StudentCriteria())["results"]]
        College.objects.filter(name="A College").update(partner_status="partner")
        College.objects.filter(name="B College").update(partner_status="none")
        after = [r["college"].name for r in run(StudentCriteria())["results"]]
        self.assertEqual(before, after)

    def test_partner_college_carries_a_disclosure(self):
        partner = make_college("Partner College", partner=True)
        make_course(partner)
        out = run(StudentCriteria())
        self.assertIn("commercial relationship", out["results"][0]["partner_note"])

    def test_old_verification_date_is_flagged_as_stale(self):
        old = make_college("Old College",
                           last_verified=date.today() - timedelta(days=800))
        make_course(old)
        out = run(StudentCriteria())
        self.assertTrue(out["results"][0]["stale"])

    def test_missing_verification_date_is_flagged_as_stale(self):
        college = make_college("No Date College")
        College.objects.filter(pk=college.pk).update(last_verified=None)
        make_course(College.objects.get(pk=college.pk))
        out = run(StudentCriteria())
        self.assertTrue(out["results"][0]["stale"])

    def test_every_result_explains_itself(self):
        make_course(self.college)
        out = run(StudentCriteria(budget=Decimal("900000"),
                                  education_level="class_12"))
        result = out["results"][0]
        self.assertTrue(result["reasons"])
        self.assertIn("fees", " ".join(result["reasons"]).lower())


class CollegeDataModelTests(TestCase):
    def test_new_college_defaults_are_safe(self):
        college = College.objects.create(name="X", location="Y")
        self.assertFalse(college.is_verified)
        self.assertEqual(college.partner_status, "none")
        self.assertFalse(college.is_demo)

    def test_demo_seed_is_labelled_and_safe_to_repeat(self):
        call_command("seed_careers", verbosity=0)
        call_command("seed_demo_colleges", verbosity=0)
        count = College.objects.count()
        self.assertGreaterEqual(count, 4)
        self.assertFalse(College.objects.filter(is_demo=False).exists())
        self.assertTrue(
            College.objects.filter(partner_status="partner").exists()
        )
        self.assertTrue(College.objects.filter(is_verified=False).exists())
        call_command("seed_demo_colleges", verbosity=0)
        self.assertEqual(College.objects.count(), count)


class CollegePagesTests(TestCase):
    def setUp(self):
        self.college = make_college("Visible College", location="Pune")
        make_course(self.college, name="Visible Course")
        make_college("Hidden College", published=False)

    def test_list_is_public_and_hides_unpublished(self):
        response = self.client.get(reverse("colleges"))
        self.assertContains(response, "Visible College")
        self.assertNotContains(response, "Hidden College")

    def test_list_filters_by_search_text(self):
        make_college("Other College", location="Chennai")
        response = self.client.get(reverse("colleges") + "?q=Chennai")
        self.assertContains(response, "Other College")
        self.assertNotContains(response, "Visible College")

    def test_list_filters_by_maximum_fees(self):
        cheap = make_college("Cheap College")
        make_course(cheap, name="Cheap Course", fees=50000)
        response = self.client.get(reverse("colleges") + "?max_fees=100000")
        self.assertContains(response, "Cheap College")
        self.assertNotContains(response, "Visible College")

    def test_invalid_max_fees_is_ignored_not_a_crash(self):
        response = self.client.get(reverse("colleges") + "?max_fees=abc")
        self.assertEqual(response.status_code, 200)

    def test_demo_college_shows_demo_banner(self):
        make_college("Fictional College", demo=True)
        response = self.client.get(reverse("colleges"))
        self.assertContains(response, "fictional")

    def test_unverified_college_is_labelled_not_verified(self):
        make_college("Unchecked College", verified=False)
        response = self.client.get(reverse("colleges"))
        self.assertContains(response, "Not verified yet")

    def test_detail_shows_data_quality_and_courses(self):
        response = self.client.get(
            reverse("college_detail", args=[self.college.pk])
        )
        self.assertContains(response, "Visible Course")
        self.assertContains(response, "Last verified")

    def test_partner_disclosure_is_shown_on_detail(self):
        partner = make_college("Partner College", partner=True)
        response = self.client.get(reverse("college_detail", args=[partner.pk]))
        self.assertContains(response, "commercial relationship")

    def test_unpublished_detail_is_404(self):
        hidden = College.objects.get(name="Hidden College")
        response = self.client.get(reverse("college_detail", args=[hidden.pk]))
        self.assertEqual(response.status_code, 404)


class CollegeRecommendPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "student1", password="StrongPass#123"
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            full_name="Asha Verma",
            current_education="Class 12 science",
            preferred_location="Pune",
            budget=Decimal("500000"),
        )
        pune = make_college("Pune College", location="Pune")
        chennai = make_college("Chennai College", location="Chennai")
        make_course(pune, name="Pune Course", fees=400000)
        make_course(chennai, name="Costly Course", fees=900000)
        make_college("Unverified College", verified=False)
        self.client.login(username="student1", password="StrongPass#123")

    def get(self, query=""):
        return self.client.get(reverse("college_recommend") + query)

    def test_requires_login(self):
        self.client.logout()
        response = self.get()
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_shows_matching_college_and_excludes_with_reason(self):
        response = self.get()
        self.assertContains(response, "Pune Course")
        self.assertContains(response, "Costly Course")
        self.assertContains(response, "above your budget")

    def test_unverified_colleges_are_hidden_but_counted(self):
        response = self.get()
        self.assertNotContains(response, "Unverified College")
        self.assertContains(response, "not verified yet")

    def test_page_never_guarantees_admission(self):
        response = self.get()
        self.assertContains(response, "does not guarantee admission")
        self.assertContains(response, "career counsellor")

    def test_what_if_budget_changes_results_without_saving_profile(self):
        response = self.get("?budget=1000000")
        self.assertContains(response, "Costly Course")
        self.assertContains(response, "Compared with your saved profile")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.budget, Decimal("500000"))

    def test_invalid_what_if_budget_falls_back_to_profile(self):
        response = self.get("?budget=abc")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pune Course")

    def test_page_works_without_a_profile(self):
        StudentProfile.objects.filter(user=self.user).delete()
        response = self.get()
        self.assertEqual(response.status_code, 200)


class AssistantCollegeLinksTests(TestCase):
    def test_colleges_option_links_to_the_recommendation_page(self):
        User.objects.create_user("student1", password="StrongPass#123")
        self.client.login(username="student1", password="StrongPass#123")
        response = self.client.get(reverse("assistant"))
        self.assertContains(response, reverse("college_recommend"))
        self.assertContains(response, reverse("colleges"))


class CollegeAdminTests(TestCase):
    def setUp(self):
        User.objects.create_superuser("boss", "b@example.com", "StrongPass#123")
        self.client.login(username="boss", password="StrongPass#123")

    def test_college_admin_pages_load(self):
        college = make_college()
        self.assertEqual(
            self.client.get("/admin/core/college/").status_code, 200
        )
        self.assertEqual(
            self.client.get("/admin/core/college/add/").status_code, 200
        )
        self.assertEqual(
            self.client.get(f"/admin/core/college/{college.pk}/change/").status_code,
            200,
        )

    def test_mark_verified_action_sets_flag_and_date(self):
        college = make_college(verified=False)
        College.objects.filter(pk=college.pk).update(last_verified=None)
        self.client.post("/admin/core/college/", {
            "action": "mark_verified_today",
            "_selected_action": [college.pk],
        })
        college.refresh_from_db()
        self.assertTrue(college.is_verified)
        self.assertEqual(college.last_verified, date.today())
