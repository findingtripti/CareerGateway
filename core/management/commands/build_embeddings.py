"""Build or refresh the embeddings used by retrieval (PDF section 16).

    python manage.py build_embeddings          only new or changed records
    python manage.py build_embeddings --force  every record again

Needs LLM_PROVIDER=gemini and GEMINI_API_KEY in .env. Only public record text
is sent. Records that are no longer published are removed. Safe to run again:
it resumes where it stopped if the free quota ran out.
"""

import time

from django.core.management.base import BaseCommand, CommandError

from core import embeddings
from core.models import RecordEmbedding
from core.retrieval import build_documents


class Command(BaseCommand):
    help = "Create or refresh embeddings for all published records."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true",
                            help="Embed every record again.")
        parser.add_argument("--pause", type=float, default=2.0,
                            help="Seconds to wait between batches (free quota).")

    def handle(self, *args, **options):
        if not embeddings.is_enabled():
            raise CommandError(
                "Embeddings are off. Set LLM_PROVIDER=gemini and GEMINI_API_KEY "
                "in .env (and do not set EMBEDDINGS=off)."
            )

        model, dims = embeddings.model_name(), embeddings.dimensions()
        docs = build_documents()
        existing = {row.source_key: row for row in RecordEmbedding.objects.all()}
        live = {doc["url"] for doc in docs}

        removed = 0
        for key in set(existing) - live:
            existing[key].delete()
            removed += 1

        todo = []
        for doc in docs:
            text = doc["embed_text"]
            digest = embeddings.text_hash(text)
            row = existing.get(doc["url"])
            current = (row is not None and row.text_hash == digest
                       and row.model == model and row.dimensions == dims)
            if options["force"] or not current:
                todo.append((doc, text, digest))

        if not todo:
            self.stdout.write(
                f"Nothing to do: {len(docs)} record(s) are up to date "
                f"({removed} removed)."
            )
            return

        done = 0
        for start in range(0, len(todo), embeddings.BATCH_SIZE):
            batch = todo[start:start + embeddings.BATCH_SIZE]
            try:
                vectors = embeddings.embed_texts(
                    [(doc["title"], text) for doc, text, _ in batch],
                    role="document",
                )
            except embeddings.EmbeddingError as exc:
                raise CommandError(
                    f"Stopped after {done} of {len(todo)} record(s): {exc}. "
                    "Run the command again later; finished records are kept."
                )
            for (doc, text, digest), vector in zip(batch, vectors):
                RecordEmbedding.objects.update_or_create(
                    source_key=doc["url"],
                    defaults={
                        "kind": doc["kind"], "title": doc["title"],
                        "text_hash": digest, "model": model,
                        "dimensions": dims, "vector": vector,
                    },
                )
            done += len(batch)
            self.stdout.write(f"  embedded {done} of {len(todo)}")
            if start + embeddings.BATCH_SIZE < len(todo) and options["pause"]:
                time.sleep(options["pause"])

        self.stdout.write(self.style.SUCCESS(
            f"{done} record(s) embedded with {model} ({dims} dimensions), "
            f"{removed} removed, {len(docs)} published in total."
        ))
