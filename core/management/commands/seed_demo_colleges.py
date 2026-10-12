from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Career, College, Course

DEMO_NOTE = (
    "Fictional demonstration record written by the project team. "
    "Not a real college. Replace with verified data before real use."
)

PARTNER_TEXT = (
    "Career Gateway has a commercial relationship with this college. "
    "This does not affect how colleges are ordered."
)

# (name, location, verified, verified_days_ago, partner, courses)
# course = (name, min_education, fees, duration, exam, career slugs)
DEMO_COLLEGES = [
    (
        "Riverbend Institute of Technology", "Pune", True, 30, False,
        [
            ("B.Tech Computer Science", "class_12", 380000, "4 years",
             "Fictional Entrance Test", ["software-development", "data-science"]),
            ("B.Tech Information Security", "class_12", 420000, "4 years",
             "Fictional Entrance Test", ["cybersecurity", "digital-forensics"]),
        ],
    ),
    (
        "Lakeside University (Demo)", "Chennai", True, 120, True,
        [
            ("BCA Cloud Computing", "class_12", 210000, "3 years",
             "Merit based", ["cloud-computing", "software-development"]),
            ("M.Sc. Data Science", "graduate", 520000, "2 years",
             "Fictional Postgraduate Test", ["data-science"]),
        ],
    ),
    (
        "Hillview Design College", "Bengaluru", True, 500, False,
        [
            ("B.Des Interaction Design", "class_12", 650000, "4 years",
             "Design aptitude test", ["ui-ux-design"]),
        ],
    ),
    (
        "Northfield Business School", "Delhi", False, None, False,
        [
            ("BBA Technology Management", "class_12", None, "3 years",
             "", ["product-management", "technology-consulting"]),
        ],
    ),
]


class Command(BaseCommand):
    help = (
        "Add FICTIONAL demo colleges so the college pages can be tried. "
        "Safe to run again. Never use this data as real college information."
    )

    def handle(self, *args, **options):
        added = 0
        for name, location, verified, days_ago, partner, courses in DEMO_COLLEGES:
            college, created = College.objects.get_or_create(
                name=name,
                defaults={
                    "location": location,
                    "description": "Fictional college for demonstration.",
                    "is_verified": verified,
                    "last_verified": (
                        date.today() - timedelta(days=days_ago)
                        if days_ago is not None else None
                    ),
                    "source_note": DEMO_NOTE,
                    "is_demo": True,
                    "partner_status": "partner" if partner else "none",
                    "partner_disclosure": PARTNER_TEXT if partner else "",
                    "scholarships": "Demo data: no scholarship information.",
                    "hostel_info": "Demo data: no hostel information.",
                    "placement_info": "Demo data: no placement information.",
                },
            )
            if not created:
                continue
            added += 1
            for cname, level, fees, duration, exam, slugs in courses:
                course = Course.objects.create(
                    college=college,
                    name=cname,
                    min_education=level,
                    fees=Decimal(fees) if fees is not None else None,
                    duration=duration,
                    entrance_exam=exam,
                )
                course.related_careers.set(Career.objects.filter(slug__in=slugs))

        self.stdout.write(self.style.SUCCESS(
            f"{added} demo college(s) added, "
            f"{len(DEMO_COLLEGES) - added} already present."
        ))
