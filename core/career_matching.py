"""Transparent career matching shared by the careers page and the assistant.

The result is an exploratory signal, never a suitability score. Every result
carries the matched words so the page can explain why it was shown.
"""

import re

PROFILE_TEXT_FIELDS = (
    "current_education",
    "academic_background",
    "subjects_and_interests",
    "skills",
    "career_interests",
    "career_goals",
)


def build_profile_text(profile):
    """Join the profile fields used for matching into one lowercase string."""
    if not profile:
        return ""
    parts = [getattr(profile, field) or "" for field in PROFILE_TEXT_FIELDS]
    return " ".join(part for part in parts if part.strip()).lower()


def find_matches(keywords, text):
    """Return the keywords found in text as whole words or phrases.

    Whole-word matching stops short keywords such as "ui" from matching
    inside unrelated words such as "building".
    """
    text = (text or "").lower()
    found = []
    for keyword in keywords:
        pattern = r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"
        if re.search(pattern, text):
            found.append(keyword)
    return found


def rank_careers(
    careers,
    profile_text="",
    interest_text="",
    priority="",
    less_coding=False,
):
    """Rank careers and report which ones a hard preference excluded.

    Returns (ranked, excluded):
      ranked   - list of dicts with career, profile_matches, answer_matches,
                 priority_match and score, best first
      excluded - careers removed because of the "less coding" preference
    """
    ranked = []
    excluded = []

    for career in careers:
        if less_coding and career.coding_intensity == "high":
            excluded.append(career)
            continue

        keywords = career.keyword_list
        profile_matches = find_matches(keywords, profile_text)
        answer_matches = find_matches(keywords, interest_text)
        priority_match = bool(priority) and priority == career.priority_tag

        score = len(profile_matches) * 2 + len(answer_matches) * 3
        if priority_match:
            score += 3

        ranked.append({
            "career": career,
            "profile_matches": profile_matches,
            "answer_matches": answer_matches,
            "priority_match": priority_match,
            "score": score,
        })

    ranked.sort(key=lambda result: result["score"], reverse=True)
    return ranked, excluded


def explain_match(result, priority_label=""):
    """Plain-language reason why a career was shown."""
    profile_matches = result["profile_matches"]
    answer_matches = result["answer_matches"]

    if profile_matches and answer_matches:
        shared = list(dict.fromkeys(profile_matches + answer_matches))[:3]
        return (
            "Your profile and current answer both relate to: "
            + ", ".join(shared)
        )
    if answer_matches:
        return (
            "Based on your answer, related interests include: "
            + ", ".join(answer_matches[:3])
        )
    if profile_matches:
        return (
            "Based on your saved profile, related areas include: "
            + ", ".join(profile_matches[:3])
        )
    if result["priority_match"]:
        return (
            "This option aligns with your selected priority: "
            + priority_label
            + ". Explore its daily work and required skills."
        )
    return (
        result["career"].summary
        + " Explore its daily work and required skills to see whether "
        "it suits you."
    )
