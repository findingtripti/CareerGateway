

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import StudentProfile
from django.contrib.auth.decorators import login_required

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
            user = User.objects.create_user(
                username=username,
                password=password,
            )
            messages.success(request, "Account created successfully. Please log in.")
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
            return redirect("home")

        messages.error(request, "Invalid username or password.")

    return render(request, "core/login.html", {"user": request.user})


def student_logout(request):
    if request.method == "POST":
        logout(request)
        return redirect("home")

    return redirect("home")

@login_required(login_url="login")
def student_profile(request):
    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        age = request.POST.get("age", "").strip()
        academic_background = request.POST.get(
    "academic_background", ""
        ).strip()
        
        skills = request.POST.get("skills", "").strip()

        current_education = request.POST.get(
            "current_education", ""
        ).strip()

        subjects_and_interests = request.POST.get(
    "subjects_and_interests", ""
        ).strip()

        preferred_location = request.POST.get(
         "preferred_location", ""
        ).strip()

        budget = request.POST.get("budget", "").strip()

        entrance_exams = request.POST.get("entrance_exams", "").strip()

        career_goals = request.POST.get("career_goals", "").strip()

        
        career_interests = request.POST.get(
    "career_interests", ""
         ).strip()

        if full_name:
            profile.full_name = full_name

        if age:
            if age.isdigit() and 1 <= int(age) <= 120:
                profile.age = int(age)
        else:
            messages.error(
                request,
                 "Please enter a valid age between 1 and 120."
            )
            return render(
                request,
               "core/profile.html",
               {"profile": profile}
            )

        
        if academic_background:
             profile.academic_background = academic_background

        if skills:
             profile.skills = skills

        if current_education:
            profile.current_education = current_education

        if subjects_and_interests:
           profile.subjects_and_interests = subjects_and_interests

        if career_interests:
           profile.career_interests = career_interests

        if preferred_location:
            profile.preferred_location = preferred_location

        if entrance_exams:
            profile.entrance_exams = entrance_exams

        if career_goals:
            profile.career_goals = career_goals

        if budget:
            try:
                 from decimal import Decimal, InvalidOperation

                 budget_value = Decimal(budget)

                 if budget_value < 0:
                     messages.error(request, "Budget cannot be negative.")
                     return render(
                         request,
                          "core/profile.html",
                          {"profile": profile}
                     )

                 profile.budget = budget

                 
            except InvalidOperation:
                messages.error(request, "Please enter a valid budget amount.")
                return render(
                    request,
                    "core/profile.html",
                    {"profile": profile}
                )
                

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
            "description": "Design, build, test, and maintain software applications.",
            "skills": "Python, programming, problem-solving",
            "pathway": "Computer Science degree or relevant skill-based learning",
            "roles": "Software Developer, Web Developer, Application Developer",
            "keywords": [
                "software", "developer", "programming", "coding",
                "python", "java", "web", "application", "computer science"
            ],
        },
        {
            "title": "Data Science",
            "description": "Use data, statistics, and computing to discover patterns and support decisions.",
            "skills": "Python, statistics, SQL, data analysis",
            "pathway": "Relevant degree plus statistics, programming, and data projects",
            "roles": "Data Analyst, Junior Data Scientist, Business Intelligence Analyst",
            "keywords": [
                "data", "analytics", "analysis", "statistics", "sql",
                "machine learning", "math", "mathematics", "research"
            ],
        },
        {
            "title": "Cybersecurity",
            "description": "Help protect systems, networks, and information from security threats.",
            "skills": "Networking, operating systems, security fundamentals",
            "pathway": "IT or computing foundations plus practical security learning",
            "roles": "Security Analyst, SOC Analyst, Security Engineer",
            "keywords": [
                "cybersecurity", "cyber security", "security", "network",
                "networking", "ethical hacking", "linux", "system", "privacy"
            ],
        },
        {
            "title": "UI/UX Design",
            "description": "Research user needs and design accessible, useful digital experiences.",
            "skills": "Design thinking, user research, prototyping",
            "pathway": "Design or related education, practice, and a portfolio",
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
