"""Show that retrieval by meaning works with the real Gemini embeddings.

    python manage.py check_embeddings
    python manage.py check_embeddings --query "how do I keep websites safe"

For each question it prints the words-only result and the words+meaning
result side by side, with the similarity of each record. Uses a few free API
calls. It never prints the key.
"""

from django.core.management.base import BaseCommand, CommandError

from core import embeddings
from core.models import RecordEmbedding
from core.retrieval import retrieve

SAMPLE_QUESTIONS = [
    "I like protecting websites from hackers",
    "which job lets me work with numbers and find patterns",
    "I enjoy fixing computers and building apps",
    "how do I run servers on the internet",
]


class Command(BaseCommand):
    help = "Compare word-only retrieval with retrieval by meaning."

    def add_arguments(self, parser):
        parser.add_argument("--query", action="append", default=[],
                            help="A question to test (can be repeated).")

    def handle(self, *args, **options):
        if not embeddings.is_enabled():
            raise CommandError("Embeddings are off (see build_embeddings).")
        stored = RecordEmbedding.objects.filter(
            model=embeddings.model_name(), dimensions=embeddings.dimensions()
        ).count()
        if not stored:
            raise CommandError("No embeddings stored. Run build_embeddings first.")

        self.stdout.write(
            f"Model {embeddings.model_name()}, {embeddings.dimensions()} dimensions, "
            f"{stored} record(s) stored, minimum similarity "
            f"{embeddings.min_similarity()}.\n"
        )
        meaning_only = 0
        for question in options["query"] or SAMPLE_QUESTIONS:
            words = retrieve(question, limit=3, use_embeddings=False)
            both = retrieve(question, limit=3, use_embeddings=True)
            self.stdout.write(f'Q: "{question}"')
            self.stdout.write("  words only : " + (
                "; ".join(r["title"] for r in words) or "(nothing found)"))
            self.stdout.write("  with meaning: " + (
                "; ".join(
                    f'{r["title"]} [{r["via"]}'
                    + (f', {r["similarity"]}' if r["similarity"] is not None else "")
                    + "]"
                    for r in both) or "(nothing found)"))
            self.stdout.write("")
            word_titles = {r["title"] for r in words}
            if any(r["via"] == "meaning" and r["title"] not in word_titles for r in both):
                meaning_only += 1

        if meaning_only:
            self.stdout.write(self.style.SUCCESS(
                f"PASS: meaning found records that word matching missed "
                f"in {meaning_only} question(s)."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "No record was found by meaning alone. Try a lower "
                "EMBEDDING_MIN_SIMILARITY in .env, or other questions."
            ))
