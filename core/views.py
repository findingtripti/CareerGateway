from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.http import url_has_allowed_host_and_scheme

from .assistant_options import (
    OPTIONS_BY_KEY,
    STARTING_OPTIONS,
    WELCOME_TEXT,
    WELCOME_TITLE,
)
from .career_matching import build_profile_text, explain_match, rank_careers
from .college_matching import (
    StudentCriteria,
    detect_education_level,
    is_stale,
    is_stale as mentor_is_stale,
    recommend_courses,
)
from .handoff import detect_triggers, triggers_for_options
from .models import Career, College, Course, Mentor, Opportunity, StudentProfile
from .opportunity_matching import (
    deadline_status,
    is_stale as opportunity_is_stale,
    match_opportunities,
)


def home(request):
    return render(request, "core/home.html")


def signup(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not password or not confirm_password:
            messages.error(request, "Please fill in all fields.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
        else:
            
            try:
                validate_password(password, user=User(username=username))
            except ValidationError as error:
                for message in error.messages:
                    messages.error(request, message)
                return render(request, "core/signup.html")

            User.objects.create_user(
                username=username,
                password=password,
            )
            messages.success(
                request,
                "Account created successfully. Please log in."
            )
            return redirect("login")

    return render(request, "core/signup.html")


def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)

            next_url = request.GET.get("next","")
            if url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect("home")

        messages.error(request, "Invalid username or password.")

    return render(request, "core/login.html", {"user": request.user})


def student_logout(request):
    if request.method == "POST":
        logout(request)
        return redirect("home")

    return redirect("home")

PROFILE_TEXT_FIELDS = [
    "full_name",
    "current_education",
    "academic_background",
    "subjects_and_interests",
    "skills",
    "career_interests",
    "preferred_location",
    "entrance_exams",
    "career_goals",
]

# Budget column is DecimalField(max_digits=12, decimal_places=2).
MAX_BUDGET = Decimal("9999999999.99")


@login_required(login_url="login")
def student_profile(request):
    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        # Only fields present in the request are changed. A field that is
        # present but empty is cleared; a field that is absent is untouched.
        for field in PROFILE_TEXT_FIELDS:
            if field in request.POST:
                setattr(profile, field, request.POST[field].strip())

        if "age" in request.POST:
            age = request.POST["age"].strip()

            if not age:
                profile.age = None
            elif not age.isdigit() or not 1 <= int(age) <= 120:
                messages.error(
                    request,
                    "Please enter a valid age between 1 and 120."
                )
                return render(
                    request,
                    "core/profile.html",
                    {"profile": profile}
                )
            else:
                profile.age = int(age)

        if "budget" in request.POST:
            budget = request.POST["budget"].strip()

            if not budget:
                profile.budget = None
            else:
                try:
                    budget_value = Decimal(budget)
                except InvalidOperation:
                    budget_value = None

                if budget_value is None or not budget_value.is_finite():
                    messages.error(
                        request,
                        "Please enter a valid budget amount."
                    )
                    return render(
                        request,
                        "core/profile.html",
                        {"profile": profile}
                    )

                if budget_value < 0 or budget_value > MAX_BUDGET:
                    messages.error(
                        request,
                        "Budget must be between 0 and 9,999,999,999."
                    )
                    return render(
                        request,
                        "core/profile.html",
                        {"profile": profile}
                    )

                profile.budget = budget_value

        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(
        request,
        "core/profile.html",
        {"profile": profile}
    )
    
PRIORITY_LABELS = {
    "creativity": "Creativity and design",
    "problem_solving": "Technical problem-solving",
    "data": "Data and research",
    "security": "Security and investigation",
    "exploration": "Exploring different options",
}


def career_card(career):
    """Plain dictionary of one career for templates and the compare script.

    Keys such as daily_work, skills, pathway, exams and roles are read by the
    JavaScript on the careers page, so keep them stable.
    """
    return {
        "slug": career.slug,
        "title": career.title,
        "description": career.summary,
        "daily_work": career.what_professionals_do,
        "skills": career.important_skills,
        "pathway": career.career_pathway,
        "exams": career.entrance_exams,
        "roles": career.possible_roles,
        "next_step": career.first_step,
        "coding_label": career.get_coding_intensity_display(),
        "verification_label": career.get_verification_status_display(),
    }


def career_exploration(request):
    profile = None

    if request.user.is_authenticated:
        profile = StudentProfile.objects.filter(user=request.user).first()

    ranked, _ = rank_careers(
        Career.objects.filter(is_published=True),
        profile_text=build_profile_text(profile),
    )

    cards = []
    for result in ranked:
        card = career_card(result["career"])
        matches = result["profile_matches"]
        card["match_count"] = len(matches)

        if matches:
            card["match_reason"] = (
                "Related profile details: " + ", ".join(matches[:4])
            )
        else:
            card["match_reason"] = (
                "Explore this option to see whether its work "
                "and required skills fit your interests."
            )

        cards.append(card)

    return render(
        request,
        "core/careers.html",
        {"careers": cards, "profile": profile},
    )


def career_detail(request, slug):
    career = get_object_or_404(Career, slug=slug, is_published=True)

    return render(
        request,
        "core/career_detail.html",
        {
            "career": career,
            "faqs": career.faqs.all(),
            "mentors": career.mentors.filter(is_published=True),
        },
    )


@login_required(login_url="login")
def career_assistant(request):
    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    interest = ""
    priority = ""
    student_answer = ""
    less_coding = False
    recommendations = []
    excluded_titles = []
    handoff = []

    # Only known option keys are accepted; anything else is ignored.
    topic = request.GET.get("topic", "")
    if topic not in OPTIONS_BY_KEY:
        topic = ""

    if request.method == "POST":
        interest = request.POST.get("interest", "").strip()[:2000]
        priority = request.POST.get("priority", "").strip()
        less_coding = request.POST.get("less_coding") == "1"
        student_answer = interest or "No additional interests provided."
    elif topic == "unsure":
        priority = "exploration"

    profile_text = build_profile_text(profile)

    ranked, excluded = rank_careers(
        Career.objects.filter(is_published=True),
        profile_text=profile_text,
        interest_text=interest,
        priority=priority,
        less_coding=less_coding,
    )

    if request.method == "POST":
        for result in ranked[:3]:
            career = result["career"]
            recommendations.append({
                "title": career.title,
                "slug": career.slug,
                "description": career.summary,
                "reason": explain_match(
                    result, PRIORITY_LABELS.get(priority, priority)
                ),
                "skills": career.important_skills,
                "pathway": career.career_pathway,
                "next_step": career.first_step,
            })

        excluded_titles = [career.title for career in excluded]

        # PDF section 8: suggest a human counsellor, never claim one exists.
        seen = set()
        for trigger in (
            triggers_for_options(len(recommendations)) + detect_triggers(interest)
        ):
            if trigger["key"] not in seen:
                seen.add(trigger["key"])
                handoff.append(trigger)

        assistant_message = (
            "Based on the information available, here are some "
            "career paths worth exploring. Compare their daily work, "
            "skills and learning requirements before deciding."
        )

        if not interest and not profile_text and not priority:
            assistant_message = (
                "You have not shared enough information for "
                "personalised guidance yet. These are starting "
                "options. Add your interests or update your profile "
                "to get more relevant suggestions."
            )
    else:
        assistant_message = (
            "Hello! I can help you explore career paths. Tell me "
            "what subjects or activities you enjoy and what matters "
            "most to you in a future career."
        )

        if profile_text:
            assistant_message += (
                " I can also use the education, interests and skills "
                "saved in your profile."
            )

        if topic:
            assistant_message = OPTIONS_BY_KEY[topic]["response"]

    return render(
        request,
        "core/assistant.html",
        {
            "profile": profile,
            "interest": interest,
            "priority": priority,
            "less_coding": less_coding,
            "student_answer": student_answer,
            "recommendations": recommendations,
            "excluded_titles": excluded_titles,
            "handoff": handoff,
            "assistant_message": assistant_message,
            "priority_labels": PRIORITY_LABELS,
            "welcome_title": WELCOME_TITLE,
            "welcome_text": WELCOME_TEXT,
            "starting_options": STARTING_OPTIONS,
            "topic": topic,
        },
    )


def parse_money(value):
    """Return a Decimal from user text, or None if it is not a usable amount."""
    try:
        amount = Decimal((value or "").strip())
    except InvalidOperation:
        return None
    if not amount.is_finite() or amount < 0 or amount > MAX_BUDGET:
        return None
    return amount


def colleges_list(request):
    """Public list of published colleges (PDF section 7)."""
    colleges = College.objects.filter(is_published=True)

    query = request.GET.get("q", "").strip()[:100]
    if query:
        colleges = colleges.filter(
            Q(name__icontains=query)
            | Q(location__icontains=query)
            | Q(courses__name__icontains=query)
        )

    max_fees_text = request.GET.get("max_fees", "").strip()
    max_fees = parse_money(max_fees_text) if max_fees_text else None
    if max_fees is not None:
        colleges = colleges.filter(courses__fees__lte=max_fees)

    colleges = colleges.distinct().prefetch_related("courses")
    items = [
        {"college": college, "stale": is_stale(college)}
        for college in colleges
    ]

    return render(request, "core/colleges.html", {
        "items": items,
        "query": query,
        "max_fees": max_fees_text if max_fees is not None else "",
        "has_demo": any(item["college"].is_demo for item in items),
    })


def college_detail(request, pk):
    college = get_object_or_404(College, pk=pk, is_published=True)
    return render(request, "core/college_detail.html", {
        "college": college,
        "courses": college.courses.prefetch_related("related_careers"),
        "stale": is_stale(college),
    })


@login_required(login_url="login")
def college_recommend(request):
    """Explainable course and college suggestions from the verified database.

    Budget and location can be changed in the URL to explore "what if"
    without touching the saved profile.
    """
    profile = StudentProfile.objects.filter(user=request.user).first()

    saved_budget = profile.budget if profile else None
    saved_location = profile.preferred_location if profile else ""

    what_if_budget = parse_money(request.GET.get("budget", ""))
    what_if_location = request.GET.get("location", "").strip()[:150]

    budget = what_if_budget if what_if_budget is not None else saved_budget
    location = what_if_location or saved_location

    criteria = StudentCriteria(
        budget=budget,
        education_level=detect_education_level(
            profile.current_education if profile else ""
        ),
        location=location,
        interest_text=build_profile_text(profile),
    )

    colleges = College.objects.filter(is_published=True, is_verified=True)
    courses = (
        Course.objects.filter(college__in=colleges)
        .select_related("college")
        .prefetch_related("related_careers")
    )
    outcome = recommend_courses(list(courses), criteria)

    unverified_count = College.objects.filter(
        is_published=True, is_verified=False
    ).count()

    return render(request, "core/college_recommend.html", {
        "profile": profile,
        "results": outcome["results"],
        "excluded": outcome["excluded"],
        "criteria": criteria,
        "unverified_count": unverified_count,
        "is_what_if": (
            what_if_budget is not None or bool(what_if_location)
        ) and (budget != saved_budget or location != saved_location),
        "saved_budget": saved_budget,
        "saved_location": saved_location,
        "has_demo": any(r["college"].is_demo for r in outcome["results"]),
        "education_unknown": criteria.education_level is None,
    })


def opportunities_list(request):
    """Public list of published opportunities (PDF section 10)."""
    items = Opportunity.objects.filter(is_published=True)

    valid_types = dict(Opportunity.OPPORTUNITY_TYPES)
    kind = request.GET.get("type", "")
    if kind not in valid_types:
        kind = ""
    if kind:
        items = items.filter(opportunity_type=kind)

    query = request.GET.get("q", "").strip()[:100]
    if query:
        items = items.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
            | Q(location__icontains=query)
        )

    rows = [
        {
            "opp": opp,
            "status": deadline_status(opp.deadline),
            "stale": opportunity_is_stale(opp),
        }
        for opp in items
    ]
    return render(request, "core/opportunities.html", {
        "rows": rows,
        "types": Opportunity.OPPORTUNITY_TYPES,
        "kind": kind,
        "query": query,
        "has_demo": any(r["opp"].is_demo for r in rows),
    })


def opportunity_detail(request, pk):
    opp = get_object_or_404(Opportunity, pk=pk, is_published=True)
    return render(request, "core/opportunity_detail.html", {
        "opp": opp,
        "status": deadline_status(opp.deadline),
        "stale": opportunity_is_stale(opp),
        "careers": opp.related_careers.all(),
    })


@login_required(login_url="login")
def opportunity_recommend(request):
    """Explainable opportunity matches for the saved profile."""
    profile = StudentProfile.objects.filter(user=request.user).first()
    criteria = StudentCriteria(
        budget=None,
        education_level=detect_education_level(
            profile.current_education if profile else ""
        ),
        location=profile.preferred_location if profile else "",
        interest_text=build_profile_text(profile),
    )
    opportunities = (
        Opportunity.objects.filter(is_published=True)
        .prefetch_related("related_careers")
    )
    outcome = match_opportunities(list(opportunities), criteria)
    return render(request, "core/opportunity_recommend.html", {
        "profile": profile,
        "results": outcome["results"],
        "excluded": outcome["excluded"],
        "criteria": criteria,
        "education_unknown": criteria.education_level is None,
        "has_demo": any(r["opportunity"].is_demo for r in outcome["results"]),
    })


def mentors_list(request):
    """Public list of published mentors (PDF section 9)."""
    mentors = Mentor.objects.filter(is_published=True)

    professions = dict(Mentor.PROFESSIONS)
    profession = request.GET.get("profession", "")
    if profession not in professions:
        profession = ""
    if profession:
        mentors = mentors.filter(profession=profession)

    career_slug = request.GET.get("career", "")
    careers = Career.objects.filter(is_published=True)
    selected_career = careers.filter(slug=career_slug).first() if career_slug else None
    if selected_career:
        mentors = mentors.filter(related_careers=selected_career)

    mentors = mentors.prefetch_related("related_careers").distinct()
    return render(request, "core/mentors.html", {
        "mentors": mentors,
        "professions": Mentor.PROFESSIONS,
        "careers": careers,
        "profession": profession,
        "career_slug": selected_career.slug if selected_career else "",
        "has_demo": any(m.is_demo for m in mentors),
    })


def mentor_detail(request, pk):
    mentor = get_object_or_404(Mentor, pk=pk, is_published=True)
    return render(request, "core/mentor_detail.html", {
        "mentor": mentor,
        "careers": mentor.related_careers.filter(is_published=True),
        "stale": mentor_is_stale(mentor),
    })
