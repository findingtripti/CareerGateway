
from django.db import models


class College(models.Model):
    """College record (PDF section 7). Colleges are only recommended from
    this verified database, never from general AI knowledge."""

    PARTNER_CHOICES = [
        ("none", "No commercial relationship"),
        ("partner", "Partner college"),
    ]

    name = models.CharField(max_length=200)
    location = models.CharField(max_length=150)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    scholarships = models.TextField(
        blank=True, help_text="Scholarships the college itself offers."
    )
    hostel_info = models.TextField(blank=True)
    placement_info = models.TextField(blank=True)

    # Data quality: who checked this, when, and from where.
    is_verified = models.BooleanField(default=False)
    last_verified = models.DateField(null=True, blank=True)
    source_note = models.TextField(blank=True)
    is_demo = models.BooleanField(
        default=False,
        help_text="Fictional record used for demonstration only.",
    )
    is_published = models.BooleanField(default=True)

    # Commercial transparency (PDF section 7): partner status never
    # changes the order of results, but it is always disclosed.
    partner_status = models.CharField(
        max_length=10, choices=PARTNER_CHOICES, default="none"
    )
    partner_disclosure = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_partner(self):
        return self.partner_status == "partner"


class Course(models.Model):
    EDUCATION_CHOICES = [
        ("class_10", "Class 10 completed"),
        ("class_12", "Class 12 completed"),
        ("graduate", "Graduate (bachelor's degree)"),
    ]

    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="courses"
    )
    name = models.CharField(max_length=200)
    duration = models.CharField(max_length=100, blank=True)
    eligibility = models.TextField(blank=True)
    min_education = models.CharField(
        max_length=10,
        choices=EDUCATION_CHOICES,
        default="class_12",
        help_text="Lowest education level needed to apply.",
    )
    fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave empty if unknown. Say in notes whether per year or total.",
    )
    entrance_exam = models.CharField(max_length=200, blank=True)
    admission_process = models.TextField(blank=True)
    related_careers = models.ManyToManyField(
        "Career", blank=True, related_name="courses"
    )

    def __str__(self):
        return f"{self.name} - {self.college.name}"


class Opportunity(models.Model):
    """Scholarship, internship, competition and similar (PDF section 10)."""

    OPPORTUNITY_TYPES = [
        ("SCHOLARSHIP", "Scholarship"),
        ("INTERNSHIP", "Internship"),
        ("COMPETITION", "Competition"),
        ("FELLOWSHIP", "Fellowship"),
        ("COURSE", "Skill Development Course"),
        ("WORKSHOP", "Workshop"),
        ("EXAM", "Entrance Exam"),
        ("PROGRAM", "Career Program"),
        ("OTHER", "Other"),
    ]
    EDUCATION_CHOICES = [
        ("", "Any education level"),
        ("class_10", "Class 10 completed"),
        ("class_12", "Class 12 completed"),
        ("graduate", "Graduate (bachelor's degree)"),
    ]

    title = models.CharField(max_length=200)
    opportunity_type = models.CharField(
        max_length=20,
        choices=OPPORTUNITY_TYPES,
    )
    description = models.TextField()
    eligibility = models.TextField(blank=True)
    min_education = models.CharField(
        max_length=10, choices=EDUCATION_CHOICES, blank=True,
        help_text="Lowest education level needed. Empty means any level.",
    )
    location = models.CharField(max_length=150, blank=True)
    application_url = models.URLField(blank=True)
    deadline = models.DateField(null=True, blank=True)
    related_careers = models.ManyToManyField(
        "Career", blank=True, related_name="opportunities"
    )

    # Data quality
    is_verified = models.BooleanField(default=False)
    last_verified = models.DateField(null=True, blank=True)
    source_note = models.TextField(blank=True)
    is_demo = models.BooleanField(
        default=False,
        help_text="Fictional record used for demonstration only.",
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["deadline", "title"]

    def __str__(self):
        return self.title


from django.conf import settings


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    full_name = models.CharField(max_length=150, blank=True)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    current_education = models.CharField(max_length=150, blank=True)
    academic_background = models.TextField(blank=True)
    subjects_and_interests = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    career_interests = models.TextField(blank=True)
    preferred_location = models.CharField(max_length=150, blank=True)
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    entrance_exams = models.TextField(blank=True)
    career_goals = models.TextField(blank=True)

    def __str__(self):
        return self.full_name or self.user.username


class Career(models.Model):
    """Structured career profile (PDF section 6) used by the careers page,
    the career detail page and the assistant (PDF section 13)."""

    CODING_CHOICES = [
        ("high", "Coding-heavy"),
        ("medium", "Some coding"),
        ("low", "Little or no coding"),
    ]
    PRIORITY_CHOICES = [
        ("", "None"),
        ("creativity", "Creativity and design"),
        ("problem_solving", "Technical problem-solving"),
        ("data", "Data and research"),
        ("security", "Security and investigation"),
    ]
    VERIFICATION_CHOICES = [
        ("draft", "Draft"),
        ("needs_verification", "Needs verification"),
        ("verified", "Verified"),
    ]

    title = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    summary = models.TextField(help_text="One or two sentences.")

    # The ten information areas listed in PDF section 6.
    what_professionals_do = models.TextField()
    required_education = models.TextField()
    entrance_exams = models.TextField()
    important_skills = models.TextField()
    career_pathway = models.TextField()
    possible_roles = models.TextField()
    higher_education_options = models.TextField()
    work_environments = models.TextField()
    professional_insights = models.TextField()
    # The tenth area, FAQs, is stored in CareerFAQ.

    first_step = models.TextField(
        blank=True, help_text="A practical first step for a beginner."
    )

    # Matching helpers (transparent, used to explain recommendations).
    coding_intensity = models.CharField(
        max_length=10, choices=CODING_CHOICES, default="medium"
    )
    priority_tag = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, blank=True
    )
    keywords = models.TextField(
        blank=True,
        help_text="Comma-separated words or phrases used for matching.",
    )

    # Data quality (Master Prompt rule 4E): where the content came from
    # and whether anyone has checked it.
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_CHOICES,
        default="needs_verification",
    )
    source_note = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    last_reviewed = models.DateField(null=True, blank=True)

    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def keyword_list(self):
        return [
            word.strip().lower()
            for word in self.keywords.split(",")
            if word.strip()
        ]


class CareerFAQ(models.Model):
    career = models.ForeignKey(
        Career, on_delete=models.CASCADE, related_name="faqs"
    )
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "career FAQ"

    def __str__(self):
        return self.question
