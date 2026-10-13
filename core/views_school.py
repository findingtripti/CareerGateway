"""School version (PDF section 11).

Honest scope: this lists school programs and records a student's interest.
It does not book a seat or session. For under-18 students it collects only
the school name, a guardian-consent flag and a general consent flag, and the
staff dashboard shows counts, not names or contact details.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import SchoolProgram, SchoolRegistration

SCHOOL_NAME_LIMIT = 150


def school_home(request):
    programs = SchoolProgram.objects.filter(is_published=True)
    return render(request, "core/school.html", {
        "programs": programs,
        "has_demo": any(p.is_demo for p in programs),
    })


@login_required(login_url="login")
def school_register(request, pk):
    program = get_object_or_404(SchoolProgram, pk=pk, is_published=True)
    existing = SchoolRegistration.objects.filter(user=request.user, program=program).first()
    values = {"school_name": "", "is_under_18": False, "guardian_consent": False}

    if request.method == "POST":
        school_name = request.POST.get("school_name", "").strip()[:SCHOOL_NAME_LIMIT]
        under_18 = request.POST.get("is_under_18") == "1"
        guardian = request.POST.get("guardian_consent") == "1"
        values.update(school_name=school_name, is_under_18=under_18, guardian_consent=guardian)
        errors = []
        if not program.is_open:
            errors.append("This program has already taken place.")
        if existing:
            errors.append("You have already registered your interest in this program.")
        if not school_name:
            errors.append("Please enter your school name.")
        if under_18 and not guardian:
            errors.append("If you are under 18, a parent or guardian must agree before you register.")
        if request.POST.get("consent") != "1":
            errors.append("Please give your consent so the school team can record your interest.")
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            SchoolRegistration.objects.create(
                user=request.user, program=program, school_name=school_name,
                is_under_18=under_18, guardian_consent=guardian and under_18,
                consent_given=True,
            )
            messages.success(request, "Your interest has been recorded. The school team will share details; nothing is booked yet.")
            return redirect("school")
    return render(request, "core/school_register.html", {
        "program": program, "values": values, "existing": existing,
    })


def _is_staff(user):
    return user.is_active and user.is_staff


@user_passes_test(_is_staff, login_url="login")
def school_dashboard(request):
    programs = SchoolProgram.objects.annotate(
        total=Count("registrations"),
        minors=Count("registrations", filter=Q(registrations__is_under_18=True)),
    )
    by_school = (
        SchoolRegistration.objects.values("school_name")
        .annotate(total=Count("id"), minors=Count("id", filter=Q(is_under_18=True)))
        .order_by("-total", "school_name")
    )
    total = SchoolRegistration.objects.count()
    minors = SchoolRegistration.objects.filter(is_under_18=True).count()
    return render(request, "core/school_dashboard.html", {
        "programs": programs,
        "by_school": by_school,
        "total_registrations": total,
        "total_minors": minors,
    })
