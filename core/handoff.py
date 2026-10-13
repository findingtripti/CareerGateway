"""When to suggest a human counsellor (PDF section 8).

The PDF lists seven situations where the assistant should not try to solve
everything. Detection is a plain whole-word phrase match so the reason for a
suggestion can always be shown to the student. This only SUGGESTS a
counsellor. Nothing is requested, booked or assigned until the student
submits the request form.
"""

import re

SUGGESTED_MESSAGE = (
    "You have several reasonable options. A career counsellor can help you "
    "evaluate them in more detail."
)

TRIGGERS = [
    {
        "key": "confused",
        "label": "confusion between several options",
        "phrases": ["confused", "cant decide", "cannot decide", "torn between",
                    "not sure which", "which is better"],
    },
    {
        "key": "personalised",
        "label": "personalised guidance",
        "phrases": ["personalised guidance", "personalized guidance",
                    "personal guidance", "one on one", "talk to a counsellor",
                    "talk to a counselor", "speak to a counsellor"],
    },
    {
        "key": "important_decision",
        "label": "an important education or admission decision",
        "phrases": ["important decision", "big decision", "final decision",
                    "admission decision"],
    },
    {
        "key": "detailed_counselling",
        "label": "detailed counselling for a student or parent",
        "phrases": ["my parents", "my parent", "detailed counselling",
                    "detailed counseling", "parents want"],
    },
    {
        "key": "college_comparison",
        "label": "college comparison",
        "phrases": ["compare colleges", "college comparison",
                    "compare these colleges", "which college is better"],
    },
    {
        "key": "admission_help",
        "label": "admission assistance",
        "phrases": ["help with admission", "admission help",
                    "admission assistance", "application help",
                    "help me apply", "help with my application"],
    },
    {
        "key": "professional_judgement",
        "label": "a situation that needs professional judgement",
        "phrases": ["gap year", "should i drop", "should i quit",
                    "change my stream", "switch my stream"],
    },
]

TRIGGER_BY_KEY = {t["key"]: t for t in TRIGGERS}

# Messages shown with each trigger. The first is the PDF's own wording.
MESSAGES = {
    "confused": SUGGESTED_MESSAGE,
}
DEFAULT_MESSAGE = (
    "This looks like a situation where a career counsellor can help more "
    "than the assistant can."
)


def _stem(word):
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _normalise(text):
    """Lowercase, drop punctuation and apostrophes, and treat a plural like
    its singular, so "compare college" matches "compare colleges"."""
    text = (text or "").lower().replace("'", "").replace("\u2019", "")
    words = re.sub(r"[^a-z0-9 ]", " ", text).split()
    return " ".join(_stem(w) for w in words)


def _with_message(trigger):
    return dict(trigger, message=MESSAGES.get(trigger["key"], DEFAULT_MESSAGE))


def detect_triggers(text):
    """Return the triggers whose phrases appear as whole words in text."""
    text = _normalise(text)
    found = []
    for trigger in TRIGGERS:
        for phrase in trigger["phrases"]:
            pattern = re.escape(_normalise(phrase))
            if re.search(r"(?<![a-z0-9])" + pattern + r"(?![a-z0-9])", text):
                found.append(_with_message(trigger))
                break
    return found


def triggers_for_options(option_count):
    """Two or more reasonable options is the PDF's first trigger."""
    if option_count >= 2:
        return [_with_message(TRIGGER_BY_KEY["confused"])]
    return []


def trigger_choices():
    return [(t["key"], t["label"]) for t in TRIGGERS]
