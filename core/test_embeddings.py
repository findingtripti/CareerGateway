"""Tests for embeddings and hybrid retrieval (PDF section 16).

No test uses the internet: the Gemini call is replaced by a fake that makes
a repeatable vector from the text.
"""

import hashlib
import io
import math
import os
from unittest import mock

from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from core import embeddings, retrieval
from core.llm import LLMError
from core.models import Career, RecordEmbedding

ENV = {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key-not-real"}
DIMS = 16


def fake_vector(text):
    """Repeatable unit vector from text (different texts are far apart)."""
    digest = hashlib.sha256(text.encode()).digest()
    raw = [b - 127.5 for b in digest[:DIMS]]
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw]


def fake_embed_texts(items, role="document", delays=()):
    return [fake_vector(text) for title, text in items]


def env(**extra):
    values = dict(ENV, EMBEDDING_DIMENSIONS="128", **extra)
    return mock.patch.dict(os.environ, values)


class VectorMathTests(TestCase):
    def test_normalize_gives_unit_length(self):
        v = embeddings.normalize([3.0, 4.0])
        self.assertAlmostEqual(math.sqrt(sum(x * x for x in v)), 1.0)

    def test_zero_vector_is_rejected(self):
        with self.assertRaises(embeddings.EmbeddingError):
            embeddings.normalize([0.0, 0.0])

    def test_cosine_same_and_opposite(self):
        a = embeddings.normalize([1.0, 2.0, 3.0])
        self.assertAlmostEqual(embeddings.cosine(a, a), 1.0)
        self.assertAlmostEqual(embeddings.cosine(a, [-x for x in a]), -1.0)

    def test_cosine_of_different_sizes_is_zero(self):
        self.assertEqual(embeddings.cosine([1.0, 0.0], [1.0]), 0.0)

    def test_hash_changes_with_text(self):
        self.assertNotEqual(embeddings.text_hash("a"), embeddings.text_hash("b"))


class SettingsTests(TestCase):
    def test_off_without_a_provider(self):
        with mock.patch.dict(os.environ, {"LLM_PROVIDER": "none"}):
            self.assertFalse(embeddings.is_enabled())

    def test_on_with_gemini_and_key(self):
        with env():
            self.assertTrue(embeddings.is_enabled())

    def test_switch_off_in_env(self):
        with env(EMBEDDINGS="off"):
            self.assertFalse(embeddings.is_enabled())

    def test_off_for_ollama(self):
        with mock.patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
            self.assertFalse(embeddings.is_enabled())

    def test_dimensions_are_bounded(self):
        with mock.patch.dict(os.environ, {"EMBEDDING_DIMENSIONS": "5"}):
            self.assertEqual(embeddings.dimensions(), embeddings.DEFAULT_DIMENSIONS)
        with mock.patch.dict(os.environ, {"EMBEDDING_DIMENSIONS": "abc"}):
            self.assertEqual(embeddings.dimensions(), embeddings.DEFAULT_DIMENSIONS)


class ApiCallTests(TestCase):
    def reply(self, count, size):
        return {"embeddings": [{"values": [1.0] * size} for _ in range(count)]}

    def test_request_shape_for_embedding_001(self):
        with env(), mock.patch("core.embeddings._post_json") as post:
            post.return_value = self.reply(2, 128)
            vectors = embeddings.embed_texts([("A", "alpha"), ("B", "beta")])
        url, payload, headers = post.call_args[0]
        self.assertIn("gemini-embedding-001:batchEmbedContents", url)
        self.assertEqual(headers, {"x-goog-api-key": "test-key-not-real"})
        self.assertNotIn("test-key-not-real", url)
        first = payload["requests"][0]
        self.assertEqual(first["taskType"], "RETRIEVAL_DOCUMENT")
        self.assertEqual(first["outputDimensionality"], 128)
        self.assertEqual(first["model"], "models/gemini-embedding-001")
        self.assertEqual(first["content"]["parts"][0]["text"], "alpha")
        self.assertEqual(len(vectors), 2)

    def test_query_uses_the_query_task(self):
        with env(), mock.patch("core.embeddings._post_json") as post:
            post.return_value = self.reply(1, 128)
            embeddings.embed_texts([("", "hello")], role="query")
        self.assertEqual(post.call_args[0][1]["requests"][0]["taskType"],
                         "RETRIEVAL_QUERY")

    def test_embedding_2_puts_the_task_in_the_text(self):
        with env(GEMINI_EMBEDDING_MODEL="gemini-embedding-2"), \
                mock.patch("core.embeddings._post_json") as post:
            post.return_value = self.reply(1, 128)
            embeddings.embed_texts([("", "hello")], role="query")
        item = post.call_args[0][1]["requests"][0]
        self.assertNotIn("taskType", item)
        self.assertTrue(item["content"]["parts"][0]["text"].startswith("task: search result"))

    def test_returned_vectors_are_normalised(self):
        with env(), mock.patch("core.embeddings._post_json") as post:
            post.return_value = self.reply(1, 128)
            vector = embeddings.embed_texts([("", "x")])[0]
        self.assertAlmostEqual(math.sqrt(sum(x * x for x in vector)), 1.0)

    def test_bad_reply_raises(self):
        with env(), mock.patch("core.embeddings._post_json", return_value={"oops": 1}):
            with self.assertRaises(embeddings.EmbeddingError):
                embeddings.embed_texts([("", "x")])

    def test_wrong_count_raises(self):
        with env(), mock.patch("core.embeddings._post_json", return_value=self.reply(1, 128)):
            with self.assertRaises(embeddings.EmbeddingError):
                embeddings.embed_texts([("", "a"), ("", "b")])

    def test_wrong_size_raises(self):
        with env(), mock.patch("core.embeddings._post_json", return_value=self.reply(1, 64)):
            with self.assertRaises(embeddings.EmbeddingError):
                embeddings.embed_texts([("", "a")])

    def test_rate_limit_is_retried_then_succeeds(self):
        calls = [LLMError("HTTP 429", retryable=True), self.reply(1, 128)]

        def side_effect(*args, **kwargs):
            item = calls.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        with env(), mock.patch("core.embeddings._post_json", side_effect=side_effect), \
                mock.patch("core.embeddings.time.sleep") as sleep:
            vectors = embeddings.embed_texts([("", "a")], delays=(5,))
        self.assertEqual(len(vectors), 1)
        sleep.assert_called_once_with(5)

    def test_bad_key_is_not_retried(self):
        with env(), mock.patch(
            "core.embeddings._post_json",
            side_effect=LLMError("HTTP 400", retryable=False),
        ) as post:
            with self.assertRaises(embeddings.EmbeddingError):
                embeddings.embed_texts([("", "a")], delays=(5, 20))
        self.assertEqual(post.call_count, 1)

    def test_error_message_has_no_key(self):
        with env(), mock.patch(
            "core.embeddings._post_json", side_effect=LLMError("HTTP 400")
        ):
            with self.assertRaises(embeddings.EmbeddingError) as ctx:
                embeddings.embed_texts([("", "a")])
        self.assertNotIn("test-key-not-real", str(ctx.exception))


class EmbedQueryTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_none_when_off(self):
        with mock.patch.dict(os.environ, {"LLM_PROVIDER": "none"}):
            self.assertIsNone(embeddings.embed_query("data science"))

    def test_none_when_the_call_fails(self):
        with env(), mock.patch(
            "core.embeddings.embed_texts", side_effect=embeddings.EmbeddingError("x")
        ):
            self.assertIsNone(embeddings.embed_query("data science"))

    def test_second_identical_question_is_cached(self):
        with env(), mock.patch(
            "core.embeddings.embed_texts", return_value=[[1.0] + [0.0] * 127]
        ) as call:
            embeddings.embed_query("Data   Science")
            embeddings.embed_query("data science")
        self.assertEqual(call.call_count, 1)


class BuildAndRetrieveTests(TestCase):
    """Uses the real seed commands, so titles match the live data."""

    def setUp(self):
        cache.clear()
        call_command("seed_careers", stdout=io.StringIO())
        call_command("seed_knowledge", stdout=io.StringIO())

    def build(self, *args):
        out = io.StringIO()
        with env(), mock.patch("core.embeddings.embed_texts", side_effect=fake_embed_texts), \
                mock.patch("core.management.commands.build_embeddings.time.sleep"):
            call_command("build_embeddings", *args, stdout=out)
        return out.getvalue()

    # ---- build command

    def test_build_refuses_when_embeddings_are_off(self):
        with mock.patch.dict(os.environ, {"LLM_PROVIDER": "none"}):
            with self.assertRaises(CommandError):
                call_command("build_embeddings", stdout=io.StringIO())

    def test_build_stores_one_vector_per_published_record(self):
        self.build()
        docs = retrieval.build_documents()
        self.assertEqual(RecordEmbedding.objects.count(), len(docs))
        row = RecordEmbedding.objects.get(title="Data Science")
        self.assertEqual(row.model, "gemini-embedding-001")
        self.assertEqual(row.dimensions, 128)

    def test_second_build_does_nothing(self):
        self.build()
        self.assertIn("Nothing to do", self.build())

    def test_changed_record_is_embedded_again(self):
        self.build()
        old = RecordEmbedding.objects.get(title="Data Science").text_hash
        Career.objects.filter(title="Data Science").update(summary="A new summary about data.")
        self.build()
        self.assertNotEqual(RecordEmbedding.objects.get(title="Data Science").text_hash, old)

    def test_unpublished_record_loses_its_vector(self):
        self.build()
        Career.objects.filter(title="Data Science").update(is_published=False)
        self.build()
        self.assertFalse(RecordEmbedding.objects.filter(title="Data Science").exists())

    def test_force_embeds_everything_again(self):
        self.build()
        with env(), mock.patch(
            "core.embeddings.embed_texts", side_effect=fake_embed_texts
        ) as call, mock.patch("core.management.commands.build_embeddings.time.sleep"):
            call_command("build_embeddings", "--force", stdout=io.StringIO())
        self.assertTrue(call.called)

    def test_failure_keeps_finished_records_and_hides_the_key(self):
        calls = {"n": 0}

        def flaky(items, role="document", delays=()):
            calls["n"] += 1
            if calls["n"] == 2:
                raise embeddings.EmbeddingError("model service returned HTTP 429")
            return fake_embed_texts(items)

        with env(), mock.patch("core.embeddings.embed_texts", side_effect=flaky), \
                mock.patch("core.management.commands.build_embeddings.time.sleep"):
            with self.assertRaises(CommandError) as ctx:
                call_command("build_embeddings", stdout=io.StringIO())
        self.assertNotIn("test-key-not-real", str(ctx.exception))
        self.assertEqual(RecordEmbedding.objects.count(), embeddings.BATCH_SIZE)

    # ---- retrieval

    def test_without_vectors_retrieval_never_calls_the_api(self):
        with env(), mock.patch("core.embeddings.embed_query") as call:
            results = retrieval.retrieve("data science")
        call.assert_not_called()
        self.assertTrue(results)
        self.assertTrue(all(r["via"] == "words" for r in results))

    def test_off_gives_the_same_results_as_words_only(self):
        self.build()
        with mock.patch.dict(os.environ, {"LLM_PROVIDER": "none"}):
            off = retrieval.retrieve("data science")
        words = retrieval.retrieve("data science", use_embeddings=False)
        self.assertEqual([r["title"] for r in off], [r["title"] for r in words])

    def test_meaning_finds_a_record_that_words_miss(self):
        self.build()
        target = RecordEmbedding.objects.get(title="Data Science")
        question = "zzqx qqvv xjkl"
        self.assertEqual(retrieval.retrieve(question, use_embeddings=False), [])
        with env(), mock.patch("core.embeddings.embed_query", return_value=target.vector):
            results = retrieval.retrieve(question)
        self.assertEqual(results[0]["title"], "Data Science")
        self.assertEqual(results[0]["via"], "meaning")
        self.assertEqual(results[0]["matched"], ["similar meaning"])
        self.assertAlmostEqual(results[0]["similarity"], 1.0, places=2)
        self.assertTrue(results[0]["snippet"])
        self.assertTrue(results[0]["context"])

    def test_record_found_both_ways_is_marked_both(self):
        self.build()
        target = RecordEmbedding.objects.get(title="Data Science")
        with env(), mock.patch("core.embeddings.embed_query", return_value=target.vector):
            results = retrieval.retrieve("data science career")
        self.assertEqual(results[0]["title"], "Data Science")
        self.assertEqual(results[0]["via"], "both")

    def test_close_meaning_outranks_a_weak_word_match(self):
        self.build()
        cloud = RecordEmbedding.objects.get(title="Cloud Computing")
        # The words point to Data Science; the meaning points to Cloud Computing.
        # A high minimum keeps only the exact meaning match, so this test does
        # not depend on how the real record texts happen to be worded.
        with env(EMBEDDING_MIN_SIMILARITY="0.99"), \
                mock.patch("core.embeddings.embed_query", return_value=cloud.vector):
            results = retrieval.retrieve("data science zzqx")
        titles = [r["title"] for r in results]
        self.assertEqual(titles[0], "Cloud Computing")
        self.assertAlmostEqual(results[0]["similarity"], 1.0, places=2)
        self.assertIn("Data Science", titles)
        data_science = [r for r in results if r["title"] == "Data Science"][0]
        self.assertEqual(data_science["via"], "words")
        self.assertIsNone(data_science["similarity"])
        self.assertLess(titles.index("Cloud Computing"), titles.index("Data Science"))

    def test_word_bonus_is_small(self):
        self.assertLess(embeddings.WORD_MATCH_BONUS, 0.1)

    def test_meaning_hits_are_ordered_by_similarity(self):
        self.build()
        data = RecordEmbedding.objects.get(title="Data Science")
        cloud = RecordEmbedding.objects.get(title="Cloud Computing")
        mix = embeddings.normalize([a + 0.8 * b for a, b in zip(data.vector, cloud.vector)])
        with env(EMBEDDING_MIN_SIMILARITY="0.0"), \
                mock.patch("core.embeddings.embed_query", return_value=mix):
            results = retrieval.retrieve("zzqx qqvv xjkl")
        sims = [r["similarity"] for r in results if r["similarity"] is not None]
        self.assertEqual(sims, sorted(sims, reverse=True))
        self.assertEqual(results[0]["title"], "Data Science")

    def test_weak_similarity_is_ignored(self):
        self.build()
        target = RecordEmbedding.objects.get(title="Data Science")
        opposite = [-x for x in target.vector]
        with env(), mock.patch("core.embeddings.embed_query", return_value=opposite):
            self.assertEqual(retrieval.retrieve("zzqx qqvv xjkl"), [])

    def test_api_failure_falls_back_to_words(self):
        self.build()
        with env(), mock.patch("core.embeddings.embed_query", return_value=None):
            results = retrieval.retrieve("data science")
        self.assertTrue(results)
        self.assertTrue(all(r["via"] == "words" for r in results))

    def test_vectors_from_another_model_are_ignored(self):
        self.build()
        RecordEmbedding.objects.update(model="some-old-model")
        with env(), mock.patch("core.embeddings.embed_query") as call:
            results = retrieval.retrieve("data science")
        call.assert_not_called()
        self.assertTrue(all(r["via"] == "words" for r in results))

    def test_unpublished_records_are_never_returned_by_meaning(self):
        self.build()
        target = RecordEmbedding.objects.get(title="Data Science")
        Career.objects.filter(title="Data Science").update(is_published=False)
        with env(), mock.patch("core.embeddings.embed_query", return_value=target.vector):
            titles = [r["title"] for r in retrieval.retrieve("zzqx qqvv xjkl")]
        self.assertNotIn("Data Science", titles)

    def test_results_keep_the_fields_other_pages_use(self):
        for r in retrieval.retrieve("data science"):
            for key in ("kind", "kind_label", "title", "url", "snippet", "context",
                        "matched", "score", "verified", "demo", "last_verified"):
                self.assertIn(key, r)

    # ---- check command

    def test_check_command_reports_pass_when_meaning_helps(self):
        self.build()
        target = RecordEmbedding.objects.get(title="Data Science")
        out = io.StringIO()
        with env(), mock.patch("core.embeddings.embed_query", return_value=target.vector):
            call_command("check_embeddings", "--query", "zzqx qqvv xjkl", stdout=out)
        self.assertIn("PASS", out.getvalue())
        self.assertNotIn("test-key-not-real", out.getvalue())

    def test_check_command_needs_built_embeddings(self):
        with env():
            with self.assertRaises(CommandError):
                call_command("check_embeddings", stdout=io.StringIO())
