
from django.contrib import admin
from .models import (
    Career,
    CareerFAQ,
    College,
    Course,
    Opportunity,
    StudentProfile,
)


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "is_verified", "created_at")
    search_fields = ("name", "location")
    list_filter = ("is_verified", "location")

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "college", "duration", "fees")
    search_fields = ("name", "college__name")
    list_filter = ("college",)

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "opportunity_type",
        "deadline",
        "is_verified",
    )
    search_fields = ("title", "description")
    list_filter = ("opportunity_type", "is_verified")

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "user",
        "current_education",
        "preferred_location",
    )
    search_fields = ("full_name", "user__username")
    list_filter = ("current_education", "preferred_location")


class CareerFAQInline(admin.TabularInline):
    model = CareerFAQ
    extra = 1


@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "coding_intensity",
        "verification_status",
        "last_reviewed",
        "is_published",
    )
    list_filter = ("verification_status", "coding_intensity", "is_published")
    search_fields = ("title", "summary", "keywords")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CareerFAQInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", "summary", "is_published")}),
        ("Career information (PDF section 6)", {"fields": (
            "what_professionals_do",
            "required_education",
            "entrance_exams",
            "important_skills",
            "career_pathway",
            "possible_roles",
            "higher_education_options",
            "work_environments",
            "professional_insights",
            "first_step",
        )}),
        ("Matching helpers", {"fields": (
            "coding_intensity", "priority_tag", "keywords",
        )}),
        ("Data quality", {"fields": (
            "verification_status",
            "source_note",
            "source_url",
            "last_reviewed",
        )}),
    )
