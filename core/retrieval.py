"""Retrieval over the controlled Career Gateway knowledge base (PDF section 13).

The PDF's pattern is: student asks -> system retrieves verified information
-> the assistant responds. This module is the retrieval step. It ranks
published records with simple word overlap, so it can always say which words
matched and which record the text came from.

There is no language model and no embeddings here, so nothing in a result is
generated. Every snippet is text from a stored record. Records that are not
verified, or are fictional demo data, are returned with a label rather than
hidden, so the student can see how far to trust them.

FUTURE: an LLM could rewrite these passages into a fluent answer, and
embeddings could replace word overlap. Both would still have to answer only
from the retrieved records.
"""

import re
from urllib.parse import quote  # noqa: F401

from django.urls import reverse

from .models import Career, College, KnowledgeEntry, Mentor, Opportunity

MAX_RESULTS = 6
SNIPPET_LENGTH = 240

STOPWORDS = frozenset(
    "a an and are as at be but by can could do does for from how i in is it me "
    "my of on or should so that the their there this to was what when where "
    "which who why will with you your about want need tell please".split()
)

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


def retrieve(query, limit=MAX_RESULTS):
    """Return up to `limit` results for the question, best first.

    Each result has: kind, kind_label, title, url, snippet, matched,
    score, verified, demo, last_verified.
    """
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return []

    scored = []
    for doc in build_documents():
        title_hits = query_tokens & doc["title_tokens"]
        keyword_hits = query_tokens & doc["keyword_tokens"]
        body_hits = query_tokens & doc["body_tokens"]
        matched = title_hits | keyword_hits | body_hits
        if not matched:
            continue
        score = 3 * len(title_hits) + 2 * len(keyword_hits) + len(body_hits)
        scored.append((score, doc, matched))

    scored.sort(key=lambda item: (-item[0], item[1]["title"].lower()))

    results = []
    for score, doc, matched in scored[:limit]:
        results.append({
            "kind": doc["kind"],
            "kind_label": doc["kind_label"],
            "title": doc["title"],
            "url": doc["url"],
            "snippet": _snippet(doc["body"], matched),
            "matched": sorted(matched),
            "score": score,
            "verified": doc["verified"],
            "demo": doc["demo"],
            "last_verified": doc["last_verified"],
        })
    return results
