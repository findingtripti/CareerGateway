from datetime import date


from django.contrib import admin
from .models import (
    Career,
    CareerFAQ,
    College,
    Course,
    KnowledgeEntry,
    Lead,
    Mentor,
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


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "__str__", "lead_type", "stage", "tier", "assigned_to",
        "application_status", "created_at",
    )
    list_filter = ("lead_type", "stage", "tier", "application_status", "assigned_to")
    search_fields = ("name", "contact_email", "contact_phone", "message")
    filter_horizontal = ("shortlist",)
    readonly_fields = ("created_at", "updated_at", "consent_given", "user")
    actions = ["mark_contacted", "mark_qualified", "assign_to_me"]
    fieldsets = (
        ("Student", {"fields": ("user", "name", "contact_email", "contact_phone",
                                "consent_given")}),
        ("Request", {"fields": ("lead_type", "trigger", "message",
                                "related_college", "related_career",
                                "related_mentor")}),
        ("Journey (PDF section 14)", {"fields": (
            "stage", "assigned_to", "shortlist", "application_status",
            "internal_notes",
        )}),
        ("Revenue tier (label only, no payment)", {"fields": ("tier",)}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    @admin.action(description="Mark selected as contacted")
    def mark_contacted(self, request, queryset):
        n = queryset.filter(stage="new").update(stage="contacted")
        self.message_user(request, f"{n} lead(s) marked as contacted.")

    @admin.action(description="Mark selected as qualified")
    def mark_qualified(self, request, queryset):
        n = queryset.filter(stage__in=["new", "contacted"]).update(stage="qualified")
        self.message_user(request, f"{n} lead(s) marked as qualified.")

    @admin.action(description="Assign selected to me")
    def assign_to_me(self, request, queryset):
        n = queryset.update(assigned_to=request.user, stage="counsellor_assigned")
        self.message_user(request, f"{n} lead(s) assigned to you.")


@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ("name", "profession", "is_verified", "last_verified",
                    "is_demo", "is_published")
    list_filter = ("profession", "is_verified", "is_demo", "is_published")
    search_fields = ("name", "headline", "bio")
    filter_horizontal = ("related_careers",)
    actions = ["mark_verified_today"]
    fieldsets = (
        (None, {"fields": ("name", "profession", "headline", "bio",
                           "years_experience", "location", "languages",
                           "availability_note", "related_careers",
                           "is_published")}),
        ("Private", {"fields": ("contact_note",),
                     "description": "Never shown to students."}),
        ("Data quality", {"fields": ("is_verified", "last_verified",
                                     "source_note", "is_demo")}),
    )

    @admin.action(description="Mark selected mentors as verified today")
    def mark_verified_today(self, request, queryset):
        n = queryset.update(is_verified=True, last_verified=date.today())
        self.message_user(request, f"{n} mentor(s) marked as verified.")


@admin.register(KnowledgeEntry)
class KnowledgeEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "entry_type", "is_verified", "last_verified",
                    "is_demo", "is_published")
    list_filter = ("entry_type", "is_verified", "is_demo", "is_published")
    search_fields = ("title", "content", "keywords")
    actions = ["mark_verified_today"]
    fieldsets = (
        (None, {"fields": ("title", "entry_type", "content", "keywords",
                           "is_published")}),
        ("Data quality", {"fields": ("is_verified", "last_verified",
                                     "source_note", "source_url", "is_demo")}),
    )

    @admin.action(description="Mark selected entries as verified today")
    def mark_verified_today(self, request, queryset):
        n = queryset.update(is_verified=True, last_verified=date.today())
        self.message_user(request, f"{n} entry(ies) marked as verified.")
