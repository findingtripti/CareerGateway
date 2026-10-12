"""Transparent course and college matching (PDF section 7).

Flow from the PDF: profile -> course -> eligibility -> budget -> location ->
preferences -> colleges. All of it runs on database records with plain rules,
never on a language model, so every result can explain itself.

Rule types (Master Prompt: hard constraints vs soft preferences):
  HARD constraints exclude a course, and the reason is reported:
      - fees above the student's budget
      - education level below what the course needs
  SOFT preferences only change the order:
      - preferred location
      - a link to a career the student is interested in
  UNKNOWN information never excludes a course. It is flagged instead.

Partner status is shown to the student but is never used for ordering.
"""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from .career_matching import find_matches

EDUCATION_ORDER = {"class_10": 1, "class_12": 2, "graduate": 3}
EDUCATION_LABELS = {
    "class_10": "Class 10",
    "class_12": "Class 12",
    "graduate": "graduate level",
}

# A verification date older than this is treated as out of date.
STALE_AFTER_DAYS = 365

DEFAULT_PARTNER_NOTE = (
    "Career Gateway has a commercial relationship with this college."
)

_GRADUATE = re.compile(
    r"(?<!\w)(b\.?\s?tech|b\.?\s?sc|b\.?\s?com|bba|bca|bachelors?|"
    r"graduate|undergraduate|degree)(?!\w)"
)
_CLASS_12 = re.compile(
    r"(?<!\w)((class|grade|std|standard)\s*12|12th|xii)(?!\w)"
)
_CLASS_10 = re.compile(
    r"(?<!\w)((class|grade|std|standard)\s*10|10th)(?!\w)"
)


def detect_education_level(text):
    """Guess class_10 / class_12 / graduate from free text, else None."""
    text = (text or "").lower()
    if not text.strip():
        return None
    if _GRADUATE.search(text):
        return "graduate"
    if _CLASS_12.search(text):
        return "class_12"
    if _CLASS_10.search(text):
        return "class_10"
    return None


@dataclass
class StudentCriteria:
    budget: Optional[Decimal] = None
    education_level: Optional[str] = None
    location: str = ""
    interest_text: str = ""


def is_stale(college, today=None):
    today = today or date.today()
    if not college.last_verified:
        return True
    return (today - college.last_verified).days > STALE_AFTER_DAYS


def _money(value):
    return f"₹{Decimal(value):,.0f}"


def recommend_courses(courses, criteria):
    """Return {"results": [...], "excluded": [...]} for the given courses.

    Every result has: course, college, score, reasons, unknowns,
    partner_note, stale.
    """
    results = []
    excluded = []
    location = (criteria.location or "").strip().lower()
    interest = (criteria.interest_text or "").lower()

    for course in courses:
        college = course.college
        reasons = []
        unknowns = []
        score = 0

        # --- Hard constraint: education level -------------------------
        required = course.min_education
        if criteria.education_level is None:
            unknowns.append(
                "We could not tell your education level, so eligibility "
                "was not checked. Check the course requirements."
            )
        else:
            student_rank = EDUCATION_ORDER[criteria.education_level]
            if student_rank < EDUCATION_ORDER.get(required, 0):
                excluded.append({
                    "course": course,
                    "college": college,
                    "reason": (
                        f"Needs {EDUCATION_LABELS[required]}; your saved "
                        f"education looks like "
                        f"{EDUCATION_LABELS[criteria.education_level]}."
                    ),
                })
                continue
            reasons.append(
                f"Matches your education level "
                f"({EDUCATION_LABELS[criteria.education_level]})."
            )

        # --- Hard constraint: budget ----------------------------------
        if course.fees is None:
            unknowns.append(
                "Fees are not listed, so the budget could not be checked. "
                "Ask the college for the current fees."
            )
        elif criteria.budget is not None:
            if course.fees > criteria.budget:
                excluded.append({
                    "course": course,
                    "college": college,
                    "reason": (
                        f"Fees of {_money(course.fees)} are above your "
                        f"budget of {_money(criteria.budget)}."
                    ),
                })
                continue
            reasons.append(
                f"Fees of {_money(course.fees)} are within your budget "
                f"of {_money(criteria.budget)}."
            )
        else:
            reasons.append(
                f"Listed fees: {_money(course.fees)} (confirm whether this "
                f"is per year or for the whole course)."
            )

        # --- Soft preference: location --------------------------------
        if location:
            if location in college.location.lower():
                score += 2
                reasons.append(
                    f"In your preferred location ({college.location})."
                )
            else:
                reasons.append(
                    f"Not in your preferred location "
                    f"(it is in {college.location})."
                )

        # --- Soft preference: career interest -------------------------
        if interest:
            matched = []
            for career in course.related_careers.all():
                if find_matches(career.keyword_list, interest):
                    matched.append(career.title)
            if matched:
                score += 3
                reasons.append(
                    "Linked to a career you mentioned: "
                    + ", ".join(matched) + "."
                )

        stale = is_stale(college)
        results.append({
            "course": course,
            "college": college,
            "score": score,
            "reasons": reasons,
            "unknowns": unknowns,
            "partner_note": (
                (college.partner_disclosure or DEFAULT_PARTNER_NOTE)
                if college.is_partner else ""
            ),
            "stale": stale,
        })

    # Order by preference score only; ties break alphabetically so partner
    # status can never decide the order.
    results.sort(
        key=lambda r: (-r["score"], r["college"].name, r["course"].name)
    )
    return {"results": results, "excluded": excluded}
