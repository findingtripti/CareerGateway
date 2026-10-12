from django.core.management.base import BaseCommand

from core.careers_seed import CAREERS, SOURCE_NOTE
from core.models import Career, CareerFAQ


class Command(BaseCommand):
    help = (
        "Add the starter careers. Safe to run again: a career that already "
        "exists (same slug) is left untouched, so admin edits are kept."
    )

    def handle(self, *args, **options):
        created_count = 0

        for item in CAREERS:
            data = dict(item)
            faqs = data.pop("faqs")
            data["source_note"] = SOURCE_NOTE
            data["verification_status"] = "needs_verification"

            career, created = Career.objects.get_or_create(
                slug=data["slug"], defaults=data
            )

            if created:
                created_count += 1
                for order, (question, answer) in enumerate(faqs, start=1):
                    CareerFAQ.objects.create(
                        career=career,
                        question=question,
                        answer=answer,
                        order=order,
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"{created_count} career(s) added, "
                f"{len(CAREERS) - created_count} already present."
            )
        )
