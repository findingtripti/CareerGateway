
from django.db import models


class College(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=150)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="courses"
    )
    name = models.CharField(max_length=200)
    duration = models.CharField(max_length=100, blank=True)
    eligibility = models.TextField(blank=True)
    fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    entrance_exam = models.CharField(max_length=200, blank=True)
    admission_process = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.college.name}"


class Opportunity(models.Model):
    OPPORTUNITY_TYPES = [
        ("SCHOLARSHIP", "Scholarship"),
        ("INTERNSHIP", "Internship"),
        ("COMPETITION", "Competition"),
        ("FELLOWSHIP", "Fellowship"),
        ("COURSE", "Skill Development Course"),
        ("WORKSHOP", "Workshop"),
        ("EXAM", "Entrance Exam"),
        ("OTHER", "Other"),
    ]

    title = models.CharField(max_length=200)
    opportunity_type = models.CharField(
        max_length=20,
        choices=OPPORTUNITY_TYPES,
    )
    description = models.TextField()
    eligibility = models.TextField(blank=True)
    location = models.CharField(max_length=150, blank=True)
    application_url = models.URLField(blank=True)
    deadline = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

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