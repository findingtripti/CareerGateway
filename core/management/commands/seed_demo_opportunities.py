from datetime import date, timedelta

from django.core.management.base import BaseCommand

from core.models import Career, Opportunity

DEMO_NOTE = (
    "Fictional demonstration record written by the project team. "
    "Not a real opportunity. Replace with verified data before real use."
)

# (title, type, days to deadline or None, min education, location, careers)
DEMO = [
    ("Demo Merit Scholarship for Class 12 Students", "SCHOLARSHIP", 45, "class_12", "", []),
    ("Demo Women in Technology Scholarship", "SCHOLARSHIP", 10, "class_12", "Pune", ["software-development"]),
    ("Demo Summer Cybersecurity Internship", "INTERNSHIP", 60, "graduate", "Chennai", ["cybersecurity"]),
    ("Demo National Coding Competition", "COMPETITION", 25, "class_10", "", ["software-development", "data-science"]),
    ("Demo Design Fellowship", "FELLOWSHIP", -5, "graduate", "Bengaluru", ["ui-ux-design"]),
    ("Demo Cloud Skills Workshop", "WORKSHOP", None, "", "", ["cloud-computing"]),
    ("Demo Entrance Exam Preparation Program", "PROGRAM", 90, "class_12", "", []),
]


class Command(BaseCommand):
    help = (
        "Add FICTIONAL demo opportunities. Safe to run again. Never use "
        "this data as real scholarship or internship information."
    )

    def handle(self, *args, **options):
        added = 0
        for title, kind, days, level, location, slugs in DEMO:
            opp, created = Opportunity.objects.get_or_create(
                title=title,
                defaults={
                    "opportunity_type": kind,
                    "description": "Fictional opportunity for demonstration.",
                    "eligibility": "Demo data: no real eligibility rules.",
                    "min_education": level,
                    "location": location,
                    "deadline": (date.today() + timedelta(days=days)) if days is not None else None,
                    "is_verified": True,
                    "last_verified": date.today(),
                    "source_note": DEMO_NOTE,
                    "is_demo": True,
                },
            )
            if created:
                added += 1
                opp.related_careers.set(Career.objects.filter(slug__in=slugs))
        self.stdout.write(self.style.SUCCESS(
            f"{added} demo opportunity(ies) added, {len(DEMO) - added} already present."
        ))
