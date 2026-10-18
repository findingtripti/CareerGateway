"""Retrieval over the controlled Career Gateway knowledge base (PDF section 13).

The PDF's pattern is: student asks -> system retrieves verified information
-> the assistant responds. This module is the retrieval step.

Two signals are used:

1. Word overlap (always on). Published records are ranked by the words they
   share with the question, so it can always say which words matched.
2. Embeddings (PDF section 16, optional). If embeddings have been built with
   `python manage.py build_embeddings` and a Gemini key is configured, the
   question is also compared by MEANING with every stored record vector, and
   the two results are merged (closest meaning first). This finds records
   that use different words from the question, for example "keep websites
   safe" -> Cybersecurity.

If embeddings are off, not built, or the call fails, retrieval works exactly
as the word-overlap version did. Nothing in a result is generated: every
snippet is text from a stored record. Records that are not verified, or are
fictional demo data, are returned with a label rather than hidden.
"""

import re
from urllib.parse import quote  # noqa: F401

from django.urls import reverse

from . import embeddings
from .models import Career, College, KnowledgeEntry, Mentor, Opportunity

MAX_RESULTS = 6
SNIPPET_LENGTH = 240
CONTEXT_LENGTH = 800  # longer passage handed to the answer-writing model

STOPWORDS = frozenset(
    "a an and are as at be but by can could do does for from how i in is it me "
    "my of on or should so that the their there this to was what when where "
    "which who why will with you your about want need tell please".split()
)

# Words that describe the whole site. A record that matches only one of these
# in its body says little about the question, so it is ranked lower.
GENERIC_WORDS = frozenset(
    "college course career student school opportunity mentor information "
    "help exam program".split()
)
GENERIC_WEIGHT = 0.3

KIND_LABELS = {
    "career": "Career",
    "college": "College",
    "opportunity": "Opportunity",
    "mentor": "Mentor",
}


def _stem(word):
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def tokenize(text):
    """Lowercase words without stopwords, with simple plural handling."""
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [_stem(w) for w in words if len(w) >= 2 and w not in STOPWORDS]


def _doc(kind, kind_label, title, url, body, keywords, verified, demo,
         last_verified, note=""):
    return {
        "kind": kind,
        "kind_label": kind_label,
        "title": title,
        "url": url,
        "body": body,
        "title_tokens": set(tokenize(title)),
        "keyword_tokens": set(tokenize(" ".join(keywords))),
        "body_tokens": set(tokenize(body)),
        # Text that is turned into an embedding (see core/embeddings.py).
        "embed_text": " ".join(
            part for part in (title + ".", ", ".join(keywords) + ".", body)
            if part.strip(" .,")
        ),
        "verified": verified,
        "demo": demo,
        "last_verified": last_verified,
        "note": note,
    }


def build_documents():
    """One searchable document per published record."""
    docs = []

    for career in Career.objects.filter(is_published=True).prefetch_related("faqs"):
        faq_text = " ".join(f"{f.question} {f.answer}" for f in career.faqs.all())
        body = " ".join([
            career.summary, career.what_professionals_do,
            career.required_education, career.entrance_exams,
            career.important_skills, career.career_pathway,
            career.possible_roles, career.higher_education_options,
            career.work_environments, career.professional_insights,
            career.first_step, faq_text,
        ])
        docs.append(_doc(
            "career", "Career", career.title,
            reverse("career_detail", args=[career.slug]), body,
            career.keyword_list + [career.title],
            career.verification_status == "verified", False,
            career.last_reviewed, career.source_note,
        ))

    for college in College.objects.filter(is_published=True).prefetch_related("courses"):
        course_text = " ".join(
            f"{c.name} {c.eligibility} {c.entrance_exam} {c.admission_process}"
            for c in college.courses.all()
        )
        body = " ".join([
            college.description, college.location, college.scholarships,
            college.hostel_info, college.placement_info, course_text,
        ])
        docs.append(_doc(
            "college", "College", college.name,
            reverse("college_detail", args=[college.pk]), body,
            [college.location], college.is_verified, college.is_demo,
            college.last_verified, college.source_note,
        ))

    for opp in Opportunity.objects.filter(is_published=True):
        body = " ".join([
            opp.description, opp.eligibility, opp.location,
            opp.get_opportunity_type_display(),
        ])
        docs.append(_doc(
            "opportunity", "Opportunity", opp.title,
            reverse("opportunity_detail", args=[opp.pk]), body,
            [opp.get_opportunity_type_display()], opp.is_verified, opp.is_demo,
            opp.last_verified, opp.source_note,
        ))

    for mentor in Mentor.objects.filter(is_published=True).prefetch_related("related_careers"):
        careers = [c.title for c in mentor.related_careers.all()]
        body = " ".join([
            mentor.headline, mentor.bio, mentor.get_profession_display(),
            mentor.location, " ".join(careers),
        ])
        docs.append(_doc(
            "mentor", "Mentor", mentor.name,
            reverse("mentor_detail", args=[mentor.pk]), body,
            careers + [mentor.get_profession_display()],
            mentor.is_verified, mentor.is_demo, mentor.last_verified,
            mentor.source_note,
        ))

    type_labels = dict(KnowledgeEntry.ENTRY_TYPES)
    for entry in KnowledgeEntry.objects.filter(is_published=True):
        docs.append(_doc(
            entry.entry_type, type_labels[entry.entry_type], entry.title,
            reverse("knowledge_detail", args=[entry.pk]), entry.content,
            entry.keyword_list, entry.is_verified, entry.is_demo,
            entry.last_verified, entry.source_note,
        ))

    return docs


def _snippet(body, matched):
    """The first sentence that contains a matched word, shortened."""
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(body.split()))
    for sentence in sentences:
        if matched & set(tokenize(sentence)):
            return sentence[:SNIPPET_LENGTH].rstrip()
    return " ".join(body.split())[:SNIPPET_LENGTH].rstrip()


def _context(body, matched):
    """A few sentences around the matched words, for the language model."""
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(body.split()))
    picked = [s for s in sentences if matched & set(tokenize(s))][:4]
    text = " ".join(picked) if picked else " ".join(body.split())
    return text[:CONTEXT_LENGTH].rstrip()


def _word_ranking(docs, query_tokens):
    """[(score, doc, matched)] best first, from word overlap only."""
    scored = []
    for doc in docs:
        title_hits = query_tokens & doc["title_tokens"]
        keyword_hits = query_tokens & doc["keyword_tokens"]
        body_hits = query_tokens & doc["body_tokens"]
        matched = title_hits | keyword_hits | body_hits
        if not matched:
            continue
        score = (
            3 * len(title_hits)
            + 2 * len(keyword_hits - GENERIC_WORDS) + GENERIC_WEIGHT * len(keyword_hits & GENERIC_WORDS)
            + len(body_hits - GENERIC_WORDS) + GENERIC_WEIGHT * len(body_hits & GENERIC_WORDS)
        )
        scored.append((round(score, 2), doc, matched))
    scored.sort(key=lambda item: (-item[0], item[1]["title"].lower()))
    return scored


def _meaning_ranking(query, docs):
    """{url: similarity} for records whose meaning is close to the question.

    Empty when embeddings are off, not built, or the call fails, so the
    caller falls back to word overlap.
    """
    if not embeddings.has_vectors():
        return {}
    query_vector = embeddings.embed_query(query)
    if query_vector is None:
        return {}
    return embeddings.similar_records(
        query_vector, {doc["url"] for doc in docs}
    )


def retrieve(query, limit=MAX_RESULTS, use_embeddings=True):
    """Return up to `limit` results for the question, best first.

    Each result has: kind, kind_label, title, url, snippet, context, matched,
    score, similarity, via, verified, demo, last_verified.
    `via` is "words", "meaning" or "both".
    """
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return []

    docs = build_documents()
    word_ranked = _word_ranking(docs, query_tokens)
    meaning = _meaning_ranking(query, docs) if use_embeddings else {}

    if meaning:
        ordered = _merge(word_ranked, meaning, docs)
    else:
        ordered = [(score, doc, matched, None) for score, doc, matched in word_ranked]

    results = []
    for score, doc, matched, similarity in ordered[:limit]:
        via = ("both" if matched and similarity is not None
               else "meaning" if similarity is not None else "words")
        results.append({
            "kind": doc["kind"],
            "kind_label": doc["kind_label"],
            "title": doc["title"],
            "url": doc["url"],
            "snippet": _snippet(doc["body"], matched),
            "context": _context(doc["body"], matched),
            "matched": sorted(matched) if matched else ["similar meaning"],
            "score": score,
            "similarity": similarity,
            "via": via,
            "verified": doc["verified"],
            "demo": doc["demo"],
            "last_verified": doc["last_verified"],
        })
    return results


def _merge(word_ranked, meaning, docs):
    """Records found by meaning first, then records found only by words.

    Records found by meaning are ordered by similarity, with a small bonus
    when they also share words with the question. Similarity is the more
    reliable signal, so a weak word match does not outrank a close meaning
    match. Records found only by words keep their word-overlap order.
    """
    by_url = {doc["url"]: doc for doc in docs}
    word_info = {doc["url"]: (score, matched) for score, doc, matched in word_ranked}

    by_meaning = []
    for url, similarity in meaning.items():
        score, matched = word_info.get(url, (0.0, set()))
        bonus = embeddings.WORD_MATCH_BONUS if matched else 0.0
        by_meaning.append((similarity + bonus, by_url[url], score, matched, similarity))
    by_meaning.sort(key=lambda item: (-item[0], item[1]["title"].lower()))

    merged = [(score, doc, matched, sim) for _, doc, score, matched, sim in by_meaning]
    merged += [(score, doc, matched, None)
               for score, doc, matched in word_ranked if doc["url"] not in meaning]
    return merged
