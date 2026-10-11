
from django.contrib import admin
from .models import College, Course, Opportunity, StudentProfile


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