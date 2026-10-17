from django import template

from core.models import StudentProfile
from core.profile_capture import (
    next_question,
    progress,
    skipped_keys,
    unanswered_skipped,
)

register = template.Library()


def _profile_for(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return None
    # Never create a row just by viewing a page.
    return (StudentProfile.objects.filter(user=user).first()
            or StudentProfile(user=user))


@register.inclusion_tag("core/_profile_step.html", takes_context=True)
def profile_step_card(context):
    request = context.get("request")
    profile = _profile_for(request)
    if profile is None:
        return {"show": False}

    skipped = skipped_keys(request.session)
    question = next_question(profile, skipped)
    still_skipped = unanswered_skipped(profile, skipped)
    done, total = progress(profile)

    if question is None and not still_skipped:
        return {"show": False}

    return {
        "show": True,
        "question": question,
        "skipped_count": len(still_skipped),
        "done": done,
        "total": total,
        "percent": int(done * 100 / total),
        "csrf_token": context.get("csrf_token"),
    }


@register.inclusion_tag("core/_profile_progress.html", takes_context=True)
def profile_progress_bar(context):
    request = context.get("request")
    profile = _profile_for(request)
    if profile is None:
        return {"show": False}
    done, total = progress(profile)
    return {
        "show": True,
        "done": done,
        "total": total,
        "percent": int(done * 100 / total),
        "complete": done == total,
    }
