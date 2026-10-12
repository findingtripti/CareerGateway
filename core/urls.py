
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.student_login, name="login"),
    path("logout/", views.student_logout, name="logout"),
    path("profile/", views.student_profile, name="profile"),
    path("careers/", views.career_exploration, name="careers"),
    path("careers/<slug:slug>/", views.career_detail, name="career_detail"),
    path("assistant/", views.career_assistant, name="assistant"),

]