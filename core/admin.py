from datetime import date


from django.contrib import admin
from .models import (
    Career,
    CareerFAQ,
    College,
    Course,
    Opportunity,
    StudentProfile,
)


class CourseInline(admin.StackedInline):
    model = Course
    extra = 0
    filter_horizontal = ("related_careers",)


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "location",
        "is_verified",
        "last_verified",
        "partner_status",
        "is_demo",
        "is_published",
    )
    search_fields = ("name", "location")
    list_filter = (
        "is_verified", "partner_status", "is_demo", "is_published", "location",
    )
    inlines = [CourseInline]
    actions = ["mark_verified_today"]
    fieldsets = (
        (None, {"fields": ("name", "location", "website", "description",
                           "is_published")}),
        ("College details (PDF section 7)", {"fields": (
            "scholarships", "hostel_info", "placement_info",
        )}),
        ("Data quality", {"fields": (
            "is_verified", "last_verified", "source_note", "is_demo",
        )}),
        ("Commercial transparency", {
            "fields": ("partner_status", "partner_disclosure"),
            "description": (
                "Partner status is always shown to students. It never "
                "changes the order of recommendations."
            ),
        }),
    )

    @admin.action(description="Mark selected colleges as verified today")
    def mark_verified_today(self, request, queryset):
        updated = queryset.update(
            is_verified=True, last_verified=date.today()
        )
        self.message_user(request, f"{updated} college(s) marked as verified.")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "college", "min_education", "duration", "fees")
    search_fields = ("name", "college__name")
    list_filter = ("min_education", "college")
    filter_horizontal = ("related_careers",)


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "opportunity_type",
        "deadline",
        "is_verified",
        "last_verified",
        "is_demo",
        "is_published",
    )
    search_fields = ("title", "description")
    list_filter = (
        "opportunity_type", "is_verified", "is_demo", "is_published",
    )
    filter_horizontal = ("related_careers",)
    actions = ["mark_verified_today"]
    fieldsets = (
        (None, {"fields": ("title", "opportunity_type", "description",
                           "is_published")}),
        ("Eligibility and dates", {"fields": (
            "eligibility", "min_education", "location", "deadline",
            "application_url", "related_careers",
        )}),
        ("Data quality", {"fields": (
            "is_verified", "last_verified", "source_note", "is_demo",
        )}),
    )

    @admin.action(description="Mark selected opportunities as verified today")
    def mark_verified_today(self, request, queryset):
        updated = queryset.update(is_verified=True, last_verified=date.today())
        self.message_user(request, f"{updated} opportunity(ies) marked as verified.")


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
