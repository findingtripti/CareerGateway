"""Starting options for the Career Assistant (PDF section 3).

Each option has a response shown when the student picks it. An option with
available=False belongs to a feature that is not built yet; its response says
so honestly and never pretends that a counsellor or booking exists.

When a feature is built later, set available=True and update the response.
"""

WELCOME_TITLE = "Welcome to Career Gateway"
WELCOME_TEXT = (
    "Let's understand where you want to go and explore the paths "
    "that can take you there."
)

NOT_AVAILABLE_NOTE = (
    "This part of Career Gateway is not available yet. In the meantime "
    "you can explore career paths below."
)

COUNSELLOR_HANDOFF_TEXT = (
    "You have several reasonable options. A career counsellor can help "
    "you evaluate them in more detail."
)

STARTING_OPTIONS = [
    {
        "key": "career",
        "label": "Choosing a career",
        "description": "Explore career paths that match your interests.",
        "available": True,
        "response": (
            "Let's explore career paths. Tell us what interests you in the "
            "form below and we will suggest options to explore."
        ),
    },
    {
        "key": "course",
        "label": "Choosing a course",
        "description": "Understand courses and what they lead to.",
        "available": True,
        "url_name": "college_recommend",
        "response": (
            "Courses are matched from our verified college database using "
            "your education, budget and interests. Open the course and "
            "college suggestions to see each course with the reasons it "
            "was shown. A career counsellor can help you compare them."
        ),
    },
    {
        "key": "colleges",
        "label": "Finding colleges",
        "description": "Find colleges from a verified database.",
        "available": True,
        "url_name": "college_recommend",
        "response": (
            "College suggestions come from our verified college database, "
            "not from general AI knowledge. Open the suggestions to see why "
            "each one was shown, or browse every listed college."
        ),
    },
    {
        "key": "scholarships",
        "label": "Scholarships",
        "description": "Discover scholarships and other opportunities.",
        "available": True,
        "url_name": "opportunity_recommend",
        "response": (
            "Opportunities are matched on your education level, location, "
            "interests and the deadline. Open the matches to see why each "
            "one is shown and which ones are closing soon."
        ),
    },
    {
        "key": "professional",
        "label": "Talk to a professional",
        "description": "Get help from a counsellor or a mentor.",
        "available": False,
        "response": (
            COUNSELLOR_HANDOFF_TEXT + " Counsellor requests are not "
            "available yet, so nothing has been requested for you."
        ),
    },
    {
        "key": "roadmap",
        "label": "Build my career roadmap",
        "description": "Turn a career choice into practical next steps.",
        "available": False,
        "response": (
            "A personal roadmap works best together with a counsellor. "
            + COUNSELLOR_HANDOFF_TEXT + " Roadmaps are not available yet."
        ),
    },
    {
        "key": "unsure",
        "label": "I don't know what I want",
        "description": "Start with several options, not one answer.",
        "available": True,
        "response": (
            "That is perfectly okay, and many students start here. Share "
            "anything you enjoy, even if it seems unrelated. We will show "
            "several options to explore, not a single answer."
        ),
    },
]

OPTIONS_BY_KEY = {option["key"]: option for option in STARTING_OPTIONS}
