
from django.urls import path
from . import views, views_ask, views_leads, views_profile_step, views_school

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.student_login, name="login"),
    path("logout/", views.student_logout, name="logout"),
    path("profile/", views.student_profile, name="profile"),
    path("careers/", views.career_exploration, name="careers"),
    path("careers/<slug:slug>/", views.career_detail, name="career_detail"),
    path("assistant/", views.career_assistant, name="assistant"),
    path("assistant/profile-step/", views_profile_step.profile_step, name="profile_step"),
    path("counsellor/request/", views_leads.counsellor_request, name="counsellor_request"),
    path("requests/", views_leads.my_requests, name="my_requests"),
    path("requests/<int:pk>/thanks/", views_leads.lead_thanks, name="lead_thanks"),
    path("colleges/<int:pk>/enquire/", views_leads.college_enquiry, name="college_enquiry"),
    path("careers/<slug:slug>/enquire/", views_leads.career_enquiry, name="career_enquiry"),
    path("staff/leads/", views_leads.lead_dashboard, name="lead_dashboard"),
    path("ask/", views_ask.ask, name="ask"),
    path("ask/api/", views_ask.ask_api, name="ask_api"),
    path("knowledge/<int:pk>/", views_ask.knowledge_detail, name="knowledge_detail"),
    path("mentors/", views.mentors_list, name="mentors"),
    path("mentors/<int:pk>/", views.mentor_detail, name="mentor_detail"),
    path("mentors/<int:pk>/request/", views_leads.mentor_request, name="mentor_request"),
    path("opportunities/", views.opportunities_list, name="opportunities"),
    path("opportunities/for-me/", views.opportunity_recommend, name="opportunity_recommend"),
    path("opportunities/<int:pk>/", views.opportunity_detail, name="opportunity_detail"),
    path("how-it-works/", views.architecture, name="architecture"),
    path("school/", views_school.school_home, name="school"),
    path("school/<int:pk>/register/", views_school.school_register, name="school_register"),
    path("staff/school/", views_school.school_dashboard, name="school_dashboard"),
    path("colleges/", views.colleges_list, name="colleges"),
    path("colleges/recommend/", views.college_recommend, name="college_recommend"),
    path("colleges/<int:pk>/", views.college_detail, name="college_detail"),

]