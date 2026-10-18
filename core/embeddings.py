"""Embeddings for retrieval (PDF section 16: "LLM API + RAG + embeddings/vector
database").

An embedding is a list of numbers that captures the MEANING of a text. Two
texts about the same thing have vectors that point the same way, even if they
share no words. Career Gateway stores one vector per published record in the
database (model RecordEmbedding) and compares the student's question with
them by cosine similarity. For a knowledge base of this size that needs no
separate vector database; pgvector on PostgreSQL is the production upgrade.

Free Gemini API only, standard library only. The key stays in .env. Only the
question text and public record text are sent, never profile or contact data.
Every function here fails safely: on any problem the caller gets None or an
empty result and retrieval falls back to word overlap.
"""

import hashlib
import logging
import math
import os
import time
import urllib.parse

from django.core.cache import cache

from .llm import LLMError, _post_json, is_enabled as _llm_enabled, provider

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-embedding-001"
DEFAULT_DIMENSIONS = 768
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"

BATCH_SIZE = 10            # texts per request (free tier has a tokens-per-minute cap)
MAX_TEXT_CHARS = 6000      # about 1,500 tokens, inside the model's input limit
QUERY_CACHE_SECONDS = 3600
BUILD_RETRY_DELAYS = (5, 20, 60)   # seconds, for rate limits while building
QUERY_RETRY_DELAYS = ()           # no retry: a question must not wait long

WORD_MATCH_BONUS = 0.03    # small boost when a meaning hit also shares words
DEFAULT_MIN_SIMILARITY = 0.55
RELATIVE_WINDOW = 0.10     # keep hits within this distance of the best one
MAX_MEANING_HITS = 6


class EmbeddingError(Exception):
    """Embedding call failed. The message never contains the key."""


# ---------------------------------------------------------------- settings

def model_name():
    return os.environ.get("GEMINI_EMBEDDING_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def dimensions():
    try:
        value = int(os.environ.get("EMBEDDING_DIMENSIONS", DEFAULT_DIMENSIONS))
    except ValueError:
        return DEFAULT_DIMENSIONS
    return value if 128 <= value <= 3072 else DEFAULT_DIMENSIONS


def min_similarity():
    try:
        return float(os.environ.get("EMBEDDING_MIN_SIMILARITY", DEFAULT_MIN_SIMILARITY))
    except ValueError:
        return DEFAULT_MIN_SIMILARITY


def is_enabled():
    """Embeddings use the same Gemini key as the answer-writing model."""
    if os.environ.get("EMBEDDINGS", "on").strip().lower() in ("off", "0", "false", "no"):
        return False
    return provider() == "gemini" and _llm_enabled()


# ---------------------------------------------------------------- vectors

def normalize(vector):
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        raise EmbeddingError("model returned an empty vector")
    return [x / norm for x in vector]


def cosine(a, b):
    """Dot product of two unit vectors (equal to cosine similarity)."""
    if len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- API calls

def _is_v2(model):
    return "embedding-2" in model


def _prepare(text, role, title=""):
    text = " ".join((text or "").split())[:MAX_TEXT_CHARS]
    if _is_v2(model_name()):
        # gemini-embedding-2 has no taskType; the task goes in the text.
        if role == "query":
            return f"task: search result | query: {text}"
        return f"title: {title or 'none'} | text: {text}"
    return text


def _request_item(text, role, title):
    model = model_name()
    item = {
        "model": f"models/{model}",
        "content": {"parts": [{"text": _prepare(text, role, title)}]},
        "outputDimensionality": dimensions(),
    }
    if not _is_v2(model):
        item["taskType"] = "RETRIEVAL_QUERY" if role == "query" else "RETRIEVAL_DOCUMENT"
    return item


def _post(payload, delays):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    url = URL.format(model=urllib.parse.quote(model_name(), safe=""))
    attempt = 0
    while True:
        try:
            return _post_json(url, payload, {"x-goog-api-key": key})
        except LLMError as exc:
            logger.warning("Embedding call failed (try %d): %s", attempt + 1, exc)
            if not exc.retryable or attempt >= len(delays):
                raise EmbeddingError(str(exc)) from None
            time.sleep(delays[attempt])
            attempt += 1


def embed_texts(items, role="document", delays=BUILD_RETRY_DELAYS):
    """Embed a list of (title, text). Returns unit vectors in the same order."""
    if not items:
        return []
    payload = {"requests": [_request_item(text, role, title) for title, text in items]}
    data = _post(payload, delays)
    try:
        vectors = [normalize(e["values"]) for e in data["embeddings"]]
    except (KeyError, TypeError, AttributeError):
        raise EmbeddingError("model returned no embeddings") from None
    if len(vectors) != len(items):
        raise EmbeddingError("model returned the wrong number of embeddings")
    if any(len(v) != dimensions() for v in vectors):
        raise EmbeddingError("model returned vectors of an unexpected size")
    return vectors


def embed_query(query):
    """Vector for a student's question, or None. Never raises."""
    query = " ".join((query or "").split())
    if not query or not is_enabled():
        return None
    key = "emb-q-" + text_hash(f"{model_name()}|{dimensions()}|{query.lower()}")[:40]
    hit = cache.get(key)
    if hit:
        return hit
    try:
        vector = embed_texts([("", query)], role="query", delays=QUERY_RETRY_DELAYS)[0]
    except EmbeddingError:
        return None
    cache.set(key, vector, QUERY_CACHE_SECONDS)
    return vector


# ---------------------------------------------------------------- stored vectors

def _current_rows():
    from .models import RecordEmbedding
    return RecordEmbedding.objects.filter(model=model_name(), dimensions=dimensions())


def has_vectors():
    """True when embeddings are on and at least one current vector is stored."""
    if not is_enabled():
        return False
    try:
        return _current_rows().exists()
    except Exception:  # table missing before migrate, database busy, ...
        logger.warning("Could not read stored embeddings", exc_info=True)
        return False


def similar_records(query_vector, allowed_keys):
    """{source_key: similarity} for the closest stored records.

    Only records in `allowed_keys` (the currently published ones) count, and
    only those above the minimum similarity and close to the best match.
    """
    scored = []
    for source_key, vector in _current_rows().values_list("source_key", "vector"):
        if source_key in allowed_keys:
            scored.append((cosine(query_vector, vector), source_key))
    if not scored:
        return {}
    scored.sort(reverse=True)
    best = scored[0][0]
    floor = max(min_similarity(), best - RELATIVE_WINDOW)
    return {
        key: round(sim, 3)
        for sim, key in scored[:MAX_MEANING_HITS]
        if sim >= floor
    }
