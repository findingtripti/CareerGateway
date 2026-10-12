
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
    path("opportunities/", views.opportunities_list, name="opportunities"),
    path("opportunities/for-me/", views.opportunity_recommend, name="opportunity_recommend"),
    path("opportunities/<int:pk>/", views.opportunity_detail, name="opportunity_detail"),
    path("colleges/", views.colleges_list, name="colleges"),
    path("colleges/recommend/", views.college_recommend, name="college_recommend"),
    path("colleges/<int:pk>/", views.college_detail, name="college_detail"),

]