from datetime import date, timedelta

from django.core.management.base import BaseCommand

from core.models import SchoolProgram

# (title, type, description, days from today, location)
DEMO = [
    ("Demo: Career Awareness Workshop", "workshop",
     "Fictional workshop introducing career fields to school students.", 21, "School hall (demo)"),
    ("Demo: Career Assessment Session", "assessment",
     "Fictional session where students try the Career Assistant together. "
     "It is an exploration activity, not a test of suitability.", 35, "Computer lab (demo)"),
    ("Demo: Mentor Talk", "mentor_session",
     "Fictional talk by a demonstration mentor.", 49, "Auditorium (demo)"),
]


class Command(BaseCommand):
    help = "Add FICTIONAL demo school programs. Safe to run again."

    def handle(self, *args, **options):
        added = 0
        for title, kind, desc, days, place in DEMO:
            _, created = SchoolProgram.objects.get_or_create(
                title=title,
                defaults=dict(
                    program_type=kind, description=desc, location=place,
                    event_date=date.today() + timedelta(days=days),
                    is_published=True, is_demo=True,
                ),
            )
            added += created
        self.stdout.write(self.style.SUCCESS(f"Added {added} fictional school programs."))
