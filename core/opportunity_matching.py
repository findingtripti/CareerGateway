"""Transparent opportunity matching (PDF section 10).

Matching dimensions from the PDF: eligibility, education level, location,
interests and deadline.

HARD rules exclude, with a stated reason:
    - the deadline has passed
    - the student's education level is below the requirement
SOFT preferences only reorder: location, career interest.
UNKNOWN information (no deadline, unknown education) is flagged, never used
to exclude.
"""

from datetime import date, timedelta

from .career_matching import find_matches
from .college_matching import EDUCATION_LABELS, EDUCATION_ORDER, STALE_AFTER_DAYS

SOON_DAYS = 14


def deadline_status(deadline, today=None):
    """none / expired / soon / open."""
    today = today or date.today()
    if deadline is None:
        return "none"
    if deadline < today:
        return "expired"
    if (deadline - today).days <= SOON_DAYS:
        return "soon"
    return "open"


def is_stale(opportunity, today=None):
    today = today or date.today()
    if not opportunity.last_verified:
        return True
    return (today - opportunity.last_verified).days > STALE_AFTER_DAYS


def match_opportunities(opportunities, criteria, today=None):
    """Return {"results": [...], "excluded": [...]}.

    Each result has: opportunity, status, score, reasons, unknowns, stale.
    """
    today = today or date.today()
    location = (criteria.location or "").strip().lower()
    interest = (criteria.interest_text or "").lower()
    results, excluded = [], []

    for opp in opportunities:
        status = deadline_status(opp.deadline, today)
        reasons, unknowns, score = [], [], 0

        if status == "expired":
            excluded.append({
                "opportunity": opp,
                "reason": (
                    f"The deadline passed on {opp.deadline:%d %b %Y}. "
                    f"Check whether it opens again next year."
                ),
            })
            continue
        if status == "none":
            unknowns.append(
                "No deadline is listed. Check the official page for dates."
            )
        elif status == "soon":
            reasons.append(f"Closing soon: deadline {opp.deadline:%d %b %Y}.")
        else:
            reasons.append(f"Deadline {opp.deadline:%d %b %Y}.")

        required = opp.min_education
        if required:
            if criteria.education_level is None:
                unknowns.append(
                    "We could not tell your education level, so eligibility "
                    "was not checked."
                )
            elif EDUCATION_ORDER[criteria.education_level] < EDUCATION_ORDER[required]:
                excluded.append({
                    "opportunity": opp,
                    "reason": (
                        f"Needs {EDUCATION_LABELS[required]}; your saved "
                        f"education looks like "
                        f"{EDUCATION_LABELS[criteria.education_level]}."
                    ),
                })
                continue
            else:
                reasons.append(
                    f"Open to your education level "
                    f"({EDUCATION_LABELS[criteria.education_level]})."
                )

        if location and opp.location:
            if location in opp.location.lower():
                score += 2
                reasons.append(f"In your preferred location ({opp.location}).")

        if interest:
            matched = [
                c.title for c in opp.related_careers.all()
                if find_matches(c.keyword_list, interest)
            ]
            if matched:
                score += 3
                reasons.append(
                    "Linked to a career you mentioned: " + ", ".join(matched) + "."
                )

        results.append({
            "opportunity": opp,
            "status": status,
            "score": score,
            "reasons": reasons,
            "unknowns": unknowns,
            "stale": is_stale(opp, today),
        })

    far = date.max
    results.sort(key=lambda r: (-r["score"], r["opportunity"].deadline or far, r["opportunity"].title))
    return {"results": results, "excluded": excluded}
