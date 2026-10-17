"""Save one profile answer from the assistant (PDF section 4)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import StudentProfile
from .profile_capture import (
    QUESTION_BY_KEY,
    SESSION_KEY,
    clean_answer,
    skipped_keys,
)


def _back():
    # Always the assistant page; never a URL taken from the request.
    return redirect(reverse("assistant") + "#profile-step")


@login_required(login_url="login")
@require_POST
def profile_step(request):
    action = request.POST.get("action", "save")
    key = request.POST.get("field", "")

    if action == "reset":
        request.session[SESSION_KEY] = []
        return _back()

    if key not in QUESTION_BY_KEY:
        messages.error(request, "That question is not available.")
        return _back()

    skipped = skipped_keys(request.session)

    if action == "skip":
        if key not in skipped:
            skipped.append(key)
        request.session[SESSION_KEY] = skipped
        return _back()

    value, error = clean_answer(key, request.POST.get("value", ""))
    if error:
        messages.error(request, error)
        return _back()

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    setattr(profile, key, value)
    profile.save(update_fields=[key])

    if key in skipped:
        skipped.remove(key)
        request.session[SESSION_KEY] = skipped

    messages.success(request, "Saved. Thank you.")
    return _back()
