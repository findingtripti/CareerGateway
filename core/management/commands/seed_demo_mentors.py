from datetime import date, timedelta

from django.core.management.base import BaseCommand

from core.models import Career, Mentor

DEMO_NOTE = (
    "Fictional demonstration profile written by the project team. This "
    "person does not exist. Replace with real, consenting and verified "
    "mentors before real use."
)

# (name, profession, headline, years, location, careers)
DEMO = [
    ("Demo Mentor: Software Engineer", "engineer",
     "Fictional engineer who builds web applications.", 8, "Pune",
     ["software-development", "cloud-computing"]),
    ("Demo Mentor: Security Analyst", "police_defence",
     "Fictional cyber crime investigator.", 12, "Delhi",
     ["cybersecurity", "digital-forensics"]),
    ("Demo Mentor: Data Researcher", "researcher",
     "Fictional researcher who works with data and statistics.", 10, "Bengaluru",
     ["data-science"]),
    ("Demo Mentor: Design Professor", "professor",
     "Fictional professor of interaction design.", 15, "Chennai",
     ["ui-ux-design"]),
    ("Demo Mentor: Startup Founder", "entrepreneur",
     "Fictional founder of a small product company.", 9, "Mumbai",
     ["product-management", "technology-consulting"]),
    ("Demo Mentor: Finance Analyst", "finance",
     "Fictional analyst at a financial services firm.", 7, "Hyderabad", []),
]


class Command(BaseCommand):
    help = (
        "Add FICTIONAL demo mentors. Safe to run again. These people do not "
        "exist. Never present them as real mentors."
    )

    def handle(self, *args, **options):
        added = 0
        for name, profession, headline, years, location, slugs in DEMO:
            mentor, created = Mentor.objects.get_or_create(
                name=name,
                defaults={
                    "profession": profession,
                    "headline": headline,
                    "bio": "Fictional profile for demonstration.",
                    "years_experience": years,
                    "location": location,
                    "languages": "English, Hindi",
                    "availability_note": "Demo data: no real availability.",
                    "is_verified": True,
                    "last_verified": date.today() - timedelta(days=20),
                    "source_note": DEMO_NOTE,
                    "is_demo": True,
                },
            )
            if created:
                added += 1
                mentor.related_careers.set(Career.objects.filter(slug__in=slugs))
        self.stdout.write(self.style.SUCCESS(
            f"{added} demo mentor(s) added, {len(DEMO) - added} already present."
        ))
