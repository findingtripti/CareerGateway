"""Gradual profile capture inside the assistant (PDF section 4).

The assistant asks ONE profile question at a time. This module holds the
question list and the validation. It deliberately has no connection to the
LLM: the questions are fixed, and only what the student types is saved.

Validation rules match the profile page (core.views.student_profile):
age 1-120, budget 0 to 9,999,999,999.99.
"""

from decimal import Decimal, InvalidOperation

MAX_BUDGET = Decimal("9999999999.99")
MAX_TEXT_LENGTH = 500
SESSION_KEY = "profile_step_skipped"


class Question:
    def __init__(self, key, label, hint="", placeholder="", kind="text",
                 suggestions=()):
        self.key = key
        self.label = label
        self.hint = hint
        self.placeholder = placeholder
        self.kind = kind
        self.suggestions = suggestions


# Order: quick, easy answers first; longer free text last.
QUESTIONS = [
    Question("full_name", "What is your full name?",
             placeholder="e.g. Asha Verma"),
    Question("age", "How old are you?", kind="number",
             hint="Enter a number between 1 and 120."),
    Question("current_education", "What are you studying right now?",
             placeholder="e.g. Class 12 science, B.Tech first year",
             suggestions=("Class 10", "Class 11", "Class 12",
                          "Diploma", "Undergraduate", "Postgraduate")),
    Question("preferred_location", "Where would you like to study or work?",
             placeholder="e.g. Delhi, Bengaluru, Remote"),
    Question("budget", "What is your budget for fees, in rupees?",
             kind="number",
             hint="A yearly amount is fine. Leave it if you are not sure."),
    Question("entrance_exams", "Which entrance exams are you considering?",
             placeholder="e.g. JEE Main, CUET, NEET, Not decided"),
    Question("subjects_and_interests",
             "Which subjects or topics do you enjoy?",
             placeholder="e.g. Mathematics, coding, design"),
    Question("skills", "What are you already good at?",
             placeholder="e.g. Python, drawing, public speaking"),
    Question("career_interests", "Which careers interest you so far?",
             placeholder="e.g. Software development, data science"),
    Question("career_goals", "What do you hope to achieve?",
             placeholder="e.g. Become a data scientist"),
]

QUESTION_BY_KEY = {q.key: q for q in QUESTIONS}
TOTAL = len(QUESTIONS)


def clean_answer(key, raw):
    """Return (value, error). Exactly one of them is None."""
    raw = (raw or "").strip()
    if not raw:
        return None, "Please type an answer, or press Skip."

    if key == "age":
        if not raw.isdigit() or not 1 <= int(raw) <= 120:
            return None, "Please enter a valid age between 1 and 120."
        return int(raw), None

    if key == "budget":
        try:
            value = Decimal(raw)
        except InvalidOperation:
            return None, "Please enter a valid budget amount."
        if not value.is_finite():
            return None, "Please enter a valid budget amount."
        if value < 0 or value > MAX_BUDGET:
            return None, "Budget must be between 0 and 9,999,999,999."
        return value, None

    if key in QUESTION_BY_KEY:
        if len(raw) > MAX_TEXT_LENGTH:
            return None, (
                "Please keep this under %d characters." % MAX_TEXT_LENGTH
            )
        return raw, None

    return None, "That question is not available."


def is_filled(profile, key):
    value = getattr(profile, key, None)
    return value is not None and value != ""


def skipped_keys(session):
    """Skipped keys from the session, limited to known questions."""
    stored = session.get(SESSION_KEY, [])
    if not isinstance(stored, list):
        return []
    return [k for k in stored if k in QUESTION_BY_KEY]


def progress(profile):
    done = sum(1 for q in QUESTIONS if is_filled(profile, q.key))
    return done, TOTAL


def next_question(profile, skipped=()):
    for q in QUESTIONS:
        if not is_filled(profile, q.key) and q.key not in skipped:
            return q
    return None


def unanswered_skipped(profile, skipped):
    return [q for q in QUESTIONS
            if q.key in skipped and not is_filled(profile, q.key)]
