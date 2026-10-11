from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect
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
from .models import StudentProfile


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
    
def career_exploration(request):
    careers = [
        {
            "title": "Software Development",
            "description": (
                "Design, build, test, and maintain software applications."
            ),
            "skills": "Python, programming, problem-solving",
            "pathway": (
                "Computer Science degree or relevant skill-based learning"
            ),
            "daily_work": (
                "Build, test, debug, and maintain software applications "
                "with a team."
            ),
            "exams": (
                "Some engineering programmes use JEE or institution-specific "
                "entrance tests. Other learning routes may not require "
                "a separate entrance exam."
            ),
            "roles": (
                "Software Developer, Web Developer, Application Developer"
            ),
            "keywords": [
                "software", "developer", "programming", "coding",
                "python", "java", "web", "application", "computer science"
            ],
        },
        {
            "title": "Data Science",
            "description": (
                "Use data, statistics, and computing to discover patterns "
                "and support decisions."
            ),
            "skills": "Python, statistics, SQL, data analysis",
            "pathway": (
                "Relevant degree plus statistics, programming, and data projects"
            ),
            "daily_work": (
                "Analyse datasets, identify patterns, create visualisations, "
                "and support data-driven decisions."
            ),
            "exams": (
                "Depending on the programme, examples may include JEE, CUET, "
                "or institution-specific admission tests. Requirements vary."
            ),
            "roles": (
                "Data Analyst, Junior Data Scientist, "
                "Business Intelligence Analyst"
            ),
            "keywords": [
                "data", "analytics", "analysis", "statistics", "sql",
                "machine learning", "math", "mathematics", "research"
            ],
        },
        {
            "title": "Cybersecurity",
            "description": (
                "Help protect systems, networks, and information "
                "from security threats."
            ),
            "skills": "Networking, operating systems, security fundamentals",
            "pathway": (
                "IT or computing foundations plus practical security learning"
            ),
            "daily_work": (
                "Monitor systems, investigate security alerts, assess "
                "vulnerabilities, and help protect digital information."
            ),
            "exams": (
                "Depending on the programme, examples may include JEE, CUET, "
                "or institution-specific admission tests. Check the "
                "institution's requirements."
            ),
            "roles": "Security Analyst, SOC Analyst, Security Engineer",
            "keywords": [
                "cybersecurity", "cyber security", "security", "network",
                "networking", "ethical hacking", "linux", "system", "privacy"
            ],
        },
        {
            "title": "UI/UX Design",
            "description": (
                "Research user needs and design accessible, useful "
                "digital experiences."
            ),
            "skills": "Design thinking, user research, prototyping",
            "pathway": (
                "Design or related education, practice, and a portfolio"
            ),
            "daily_work": (
                "Understand user needs, create wireframes and prototypes, "
                "test designs, and improve digital experiences."
            ),
            "exams": (
                "Some design programmes use UCEED, NID DAT, or "
                "institution-specific admission processes. Check current "
                "eligibility and exam requirements."
            ),
            "roles": "UI Designer, UX Designer, Product Designer",
            "keywords": [
                "design", "ui", "ux", "creative", "creativity", "visual",
                "user experience", "product design", "prototyping"
            ],
        },
    ]

    profile = None

    if request.user.is_authenticated:
        try:
            profile = request.user.student_profile
        except StudentProfile.DoesNotExist:
            profile = None

    profile_text = ""

    if profile:
        profile_text = " ".join([
            profile.current_education or "",
            profile.academic_background or "",
            profile.subjects_and_interests or "",
            profile.skills or "",
            profile.career_interests or "",
            profile.career_goals or "",
        ]).lower()

    for career in careers:
        matched_keywords = [
            keyword
            for keyword in career["keywords"]
            if keyword in profile_text
        ]

        career["match_count"] = len(matched_keywords)

        if matched_keywords:
            career["match_reason"] = (
                "Related profile details: "
                + ", ".join(matched_keywords[:4])
            )
        else:
            career["match_reason"] = (
                "Explore this option to see whether its work "
                "and required skills fit your interests."
            )

    next_steps = {
        "Software Development": (
            "Build a small Python project, practise problem-solving, "
            "and learn Git and GitHub."
        ),
        "Data Science": (
            "Practise Python, learn basic statistics, and analyse "
            "a small dataset."
        ),
        "Cybersecurity": (
            "Learn networking fundamentals, Linux basics, and practise "
            "in a legal beginner cybersecurity lab."
        ),
        "UI/UX Design": (
            "Study usability principles and create a simple "
            "wireframe for a student-focused app."
        ),
    }

    for career in careers:
        career["next_step"] = next_steps.get(
            career["title"],
            "Explore the required skills and try a small beginner project."
        )

    careers.sort(
        key=lambda career: career["match_count"],
        reverse=True,
    )

    return render(
        request,
        "core/careers.html",
        {
            "careers": careers,
            "profile": profile,
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
    recommendations = []

    # Only known option keys are accepted; anything else is ignored.
    topic = request.GET.get("topic", "")
    if topic not in OPTIONS_BY_KEY:
        topic = ""

    career_options = [
        {
            "title": "Software Development",
            "description": (
                "Build, test and maintain websites, applications "
                "and software systems."
            ),
            "skills": "Python, programming, problem-solving",
            "roles": "Software Developer, Web Developer",
            "pathway": (
                "Learn programming fundamentals, practise Python, "
                "and build small software projects."
            ),
            "keywords": [
                "coding", "code", "programming", "python",
                "java", "software", "computer", "web",
                "problem solving",
            ],
            "reason": "This path involves building technical solutions.",
            "priority": "problem_solving",
        },
        {
            "title": "Data Science",
            "description": (
                "Use data, statistics and computing to find patterns "
                "and support decisions."
            ),
            "skills": "Python, SQL, statistics, data analysis",
            "roles": "Data Analyst, Junior Data Scientist",
            "pathway": (
                "Learn Python, SQL, statistics, and data visualisation, "
                "then practise with datasets."
            ),
            "keywords": [
                "data", "statistics", "math", "mathematics",
                "analysis", "analytics", "research", "sql",
                "machine learning",
            ],
            "reason": (
                "This path focuses on analysing data and finding insights."
            ),
            "priority": "data",
        },
        {
            "title": "Cybersecurity",
            "description": (
                "Help protect computer systems, networks and "
                "digital information."
            ),
            "skills": "Networking, Linux, security fundamentals",
            "roles": "Security Analyst, SOC Analyst",
            "pathway": (
                "Learn networking, Linux, and operating-system fundamentals, "
                "then practise using authorised security labs."
            ),
            "keywords": [
                "security", "cybersecurity", "cyber security",
                "network", "networking", "linux", "privacy",
                "ethical hacking",
            ],
            "reason": (
                "This path focuses on investigating and preventing security risks."
            ),
            "priority": "security",
        },
        {
            "title": "UI/UX Design",
            "description": (
                "Understand user needs and design useful, "
                "accessible digital experiences."
            ),
            "skills": "Design thinking, user research, prototyping",
            "roles": "UI Designer, UX Designer, Product Designer",
            "pathway": (
                "Learn user research, wireframing, prototyping, "
                "and accessibility, then build a design portfolio."
            ),
            "keywords": [
                "design", "creative", "creativity", "visual",
                "ui", "ux", "user experience", "prototyping",
                "art",
            ],
            "reason": (
                "This path combines creativity with understanding users."
            ),
            "priority": "creativity",
        },
    ]

    if request.method == "POST":
        interest = request.POST.get("interest", "").strip()[:2000]
        priority = request.POST.get("priority", "").strip()
        student_answer = interest or "No additional interests provided."
    elif topic == "unsure":
        priority = "exploration"

    profile_text = ""

    if profile:
        profile_text = " ".join([
            profile.current_education or "",
            profile.academic_background or "",
            profile.subjects_and_interests or "",
            profile.skills or "",
            profile.career_interests or "",
            profile.career_goals or "",
        ]).lower()

    combined_text = f"{profile_text} {interest.lower()}"

    priority_labels = {
        "creativity": "Creativity and design",
        "problem_solving": "Technical problem-solving",
        "data": "Data and research",
        "security": "Security and investigation",
        "exploration": "Exploring different options",
    }

    for career in career_options:
        profile_matches = [
            keyword
            for keyword in career["keywords"]
            if keyword in profile_text
        ]

        answer_matches = [
            keyword
            for keyword in career["keywords"]
            if keyword in interest.lower()
        ]

        score = 0
        score += len(profile_matches) * 2
        score += len(answer_matches) * 3

        if priority == career["priority"]:
            score += 3

        career["score"] = score

        if profile_matches and answer_matches:
            career["reason"] = (
                "Your profile and current answer both relate to: "
                + ", ".join(
                    list(dict.fromkeys(
                        profile_matches + answer_matches
                    ))[:3]
                )
            )
        elif answer_matches:
            career["reason"] = (
                "Based on your answer, related interests include: "
                + ", ".join(answer_matches[:3])
            )
        elif profile_matches:
            career["reason"] = (
                "Based on your saved profile, related areas include: "
                + ", ".join(profile_matches[:3])
            )
        elif priority == career["priority"]:
            career["reason"] = (
                "This option aligns with your selected priority: "
                + priority_labels.get(priority, priority)
                + ". Explore its daily work and required skills."
            )
        else:
            career["reason"] = (
                career["reason"]
                + " Explore its daily work and required skills "
                "to see whether it suits you."
            )

    next_steps = {
        "Software Development": (
            "Build a small Python project, practise problem-solving, "
            "and learn Git and GitHub."
        ),
        "Data Science": (
            "Practise Python, learn basic statistics, and analyse "
            "a small dataset."
        ),
        "Cybersecurity": (
            "Learn networking fundamentals, Linux basics, and practise "
            "in a legal beginner cybersecurity lab."
        ),
        "UI/UX Design": (
            "Study usability principles and create a simple "
            "wireframe for a student-focused app."
        ),
    }

    for career in career_options:
        career["next_step"] = next_steps.get(
            career["title"],
            "Explore the required skills and try a small beginner project."
        )

    career_options.sort(
        key=lambda career: career["score"],
        reverse=True,
    )

    if request.method == "POST":
        recommendations = career_options[:3]

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
            "student_answer": student_answer,
            "recommendations": recommendations,
            "assistant_message": assistant_message,
            "priority_labels": priority_labels,
            "welcome_title": WELCOME_TITLE,
            "welcome_text": WELCOME_TEXT,
            "starting_options": STARTING_OPTIONS,
            "topic": topic,
        },
    )