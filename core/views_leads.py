"""Counsellor requests, enquiries and the staff lead dashboard
(PDF sections 8 and 14).

These views only RECORD a request. They never book a session, assign a
counsellor or take payment. Contact details are shown only to the student
who sent them and to staff.
"""

import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .handoff import SUGGESTED_MESSAGE, TRIGGER_BY_KEY, trigger_choices
from .models import Career, College, Lead, StudentProfile

MESSAGE_LIMIT = 2000
_PHONE = re.compile(r"^\+?[0-9][0-9 \-]{5,18}[0-9]$")


def _clean_contact(email, phone):
    """Return (email, phone, errors)."""
    errors = []
    email = (email or "").strip()[:254]
    phone = (phone or "").strip()[:20]
    if not email and not phone:
        errors.append("Please give an email address or a phone number so the team can reach you.")
    if email:
        try:
            validate_email(email)
        except ValidationError:
            errors.append("Please enter a valid email address.")
    if phone:
        digits = re.sub(r"\D", "", phone)
        if not _PHONE.match(phone) or not 7 <= len(digits) <= 15:
            errors.append("Please enter a valid phone number.")
    return email, phone, errors


def _handle_lead_form(request, *, lead_type, template, context, related_college=None,
                      related_career=None, allow_trigger=False):
    profile = StudentProfile.objects.filter(user=request.user).first()
    values = {
        "contact_email": request.user.email or "",
        "contact_phone": "",
        "message": "",
        "trigger": request.GET.get("trigger", ""),
    }
    if request.method == "POST":
        email, phone, errors = _clean_contact(
            request.POST.get("contact_email"), request.POST.get("contact_phone")
        )
        message = request.POST.get("message", "").strip()[:MESSAGE_LIMIT]
        trigger = request.POST.get("trigger", "") if allow_trigger else ""
        if trigger not in TRIGGER_BY_KEY:
            trigger = ""
        if request.POST.get("consent") != "1":
            errors.append("Please give your consent so we may contact you about this request.")
        values.update(contact_email=email, contact_phone=phone,
                      message=message, trigger=trigger)
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            lead = Lead.objects.create(
                user=request.user,
                name=(profile.full_name if profile else "") or request.user.get_username(),
                contact_email=email,
                contact_phone=phone,
                lead_type=lead_type,
                trigger=trigger,
                message=message,
                related_college=related_college,
                related_career=related_career,
                consent_given=True,
            )
            return redirect("lead_thanks", pk=lead.pk)
    if values["trigger"] not in TRIGGER_BY_KEY:
        values["trigger"] = ""
    return render(request, template, dict(
        context, values=values, trigger_choices=trigger_choices(), profile=profile,
    ))


@login_required(login_url="login")
def counsellor_request(request):
    return _handle_lead_form(
        request, lead_type="counselling_request",
        template="core/counsellor_request.html",
        context={"suggested_message": SUGGESTED_MESSAGE},
        allow_trigger=True,
    )


@login_required(login_url="login")
def college_enquiry(request, pk):
    college = get_object_or_404(College, pk=pk, is_published=True)
    return _handle_lead_form(
        request, lead_type="college_enquiry", template="core/enquiry.html",
        context={"subject": college.name, "back_url": reverse("college_detail", args=[college.pk]),
                 "kind": "college"},
        related_college=college,
    )


@login_required(login_url="login")
def career_enquiry(request, slug):
    career = get_object_or_404(Career, slug=slug, is_published=True)
    return _handle_lead_form(
        request, lead_type="career_enquiry", template="core/enquiry.html",
        context={"subject": career.title, "back_url": reverse("career_detail", args=[career.slug]),
                 "kind": "career"},
        related_career=career,
    )


@login_required(login_url="login")
def lead_thanks(request, pk):
    lead = get_object_or_404(Lead, pk=pk, user=request.user)
    return render(request, "core/lead_thanks.html", {"lead": lead})


@login_required(login_url="login")
def my_requests(request):
    leads = Lead.objects.filter(user=request.user).select_related(
        "related_college", "related_career", "assigned_to"
    )
    return render(request, "core/my_requests.html", {"leads": leads})


def _is_staff(user):
    return user.is_active and user.is_staff


def _journey(lead, profile):
    """The PDF section 14 example: Student -> education -> interest -> budget
    -> shortlist -> counsellor -> application."""
    steps = [("Student", lead.name or (lead.user.get_username() if lead.user else "Unknown"))]
    if profile:
        if profile.current_education:
            steps.append(("Education", profile.current_education))
        if profile.career_interests:
            steps.append(("Interest", profile.career_interests))
        if profile.budget is not None:
            steps.append(("Budget", f"₹{profile.budget:,.0f}"))
    shortlisted = [c.name for c in lead.shortlist.all()]
    if shortlisted:
        steps.append(("Shortlisted colleges", ", ".join(shortlisted)))
    if lead.assigned_to:
        steps.append(("Counsellor assigned", lead.assigned_to.get_username()))
    if lead.application_status:
        steps.append(("Application", lead.get_application_status_display()))
    return steps


@user_passes_test(_is_staff, login_url="login")
def lead_dashboard(request):
    type_counts = []
    for value, label in Lead.LEAD_TYPES:
        # The PDF names these as plural headings.
        plural = {
            "student_enquiry": "Student enquiries",
            "career_enquiry": "Career enquiries",
            "college_enquiry": "College enquiries",
            "counselling_request": "Counselling requests",
            "mentor_request": "Mentor requests",
            "admission_lead": "Admission leads",
        }[value]
        type_counts.append((plural, Lead.objects.filter(lead_type=value).count()))

    stage_counts = [
        (label, Lead.objects.filter(stage=value).count())
        for value, label in Lead.STAGES
    ]
    tier_counts = [
        (label, Lead.objects.filter(tier=value).count())
        for value, label in Lead.TIERS
    ]
    unassigned = Lead.objects.filter(assigned_to__isnull=True).exclude(stage="closed").count()

    recent = list(
        Lead.objects.select_related("user", "assigned_to", "related_college", "related_career")
        .prefetch_related("shortlist")[:50]
    )
    profiles = {
        p.user_id: p
        for p in StudentProfile.objects.filter(user_id__in=[l.user_id for l in recent if l.user_id])
    }
    rows = [
        {"lead": lead, "journey": _journey(lead, profiles.get(lead.user_id))}
        for lead in recent
    ]
    return render(request, "core/lead_dashboard.html", {
        "type_counts": type_counts,
        "stage_counts": stage_counts,
        "tier_counts": tier_counts,
        "unassigned": unassigned,
        "rows": rows,
        "total": Lead.objects.count(),
    })
