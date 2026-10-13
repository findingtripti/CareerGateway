import time

from django.core.management.base import BaseCommand, CommandError

from core import llm
from core.retrieval import retrieve


class Command(BaseCommand):
    help = (
        "Ask one question through the real pipeline (retrieval, then the "
        "configured free LLM) and check that the model wrote its own answer "
        "instead of copying the retrieved text."
    )

    def add_arguments(self, parser):
        parser.add_argument("--question", default="What is an entrance exam and how do I prepare?")

    def handle(self, *args, **options):
        question = options["question"]
        if not llm.is_enabled():
            raise CommandError(
                "No model is configured. Set LLM_PROVIDER=gemini and GEMINI_API_KEY "
                "(or LLM_PROVIDER=ollama) in .env, then run this again."
            )
        results = retrieve(question)
        if not results:
            raise CommandError("Retrieval found no records for this question. Run the seed commands first.")

        self.stdout.write(f"Provider: {llm.provider()}   Model: {llm.model_name()}")
        self.stdout.write("Retrieved records:")
        for number, item in enumerate(results, start=1):
            self.stdout.write(f"  [{number}] {item['kind_label']}: {item['title']}")

        started = time.time()
        answer = llm.generate_answer(question, results, use_cache=False)
        if not answer:
            raise CommandError(
                "FAIL: the model gave no answer. Check the key, model name, internet "
                "connection (Gemini) or that Ollama is running (ollama)."
            )
        self.stdout.write(f"\nModel answer ({time.time() - started:.1f}s):\n{answer['text']}\n")

        norm = " ".join(answer["text"].lower().split())
        for item in results:
            for text in (item["snippet"], item["context"]):
                if text and " ".join(text.lower().split()) in norm:
                    raise CommandError("FAIL: the answer contains a retrieved passage word for word, so it was copied, not written.")
        self.stdout.write(self.style.SUCCESS("PASS: the model wrote its own answer from the retrieved records."))
