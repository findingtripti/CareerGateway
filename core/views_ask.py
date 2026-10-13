"""Ask Career Gateway: answers come only from stored records (PDF section 13)."""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .handoff import SUGGESTED_MESSAGE, detect_triggers
from .models import KnowledgeEntry
from . import llm
from .retrieval import retrieve

QUERY_LIMIT = 200


def _query(request):
    return request.GET.get("q", "").strip()[:QUERY_LIMIT]


def _client_id(request):
    return request.META.get("REMOTE_ADDR", "unknown")


def _answer(request, query, results):
    """Return (answer_dict_or_None, note). The model only ever sees the
    question and the retrieved records; any problem leaves the plain results."""
    if not (query and results and llm.is_enabled()):
        return None, None
    hit = llm.cached_answer(query, results)
    if hit:
        return hit, None
    if not llm.allow_call(_client_id(request)):
        return None, "busy"
    answer = llm.generate_answer(query, results)
    return (answer, None) if answer else (None, "unavailable")


@require_GET
def ask(request):
    query = _query(request)
    results = retrieve(query) if query else []
    answer, answer_note = _answer(request, query, results)
    return render(request, "core/ask.html", {
        "answer": answer,
        "answer_note": answer_note,
        "llm_on": llm.is_enabled(),
        "query": query,
        "results": results,
        "searched": bool(query),
        "handoff": detect_triggers(query) if query else [],
        "suggested_message": SUGGESTED_MESSAGE,
        "has_demo": any(r["demo"] for r in results),
    })


@require_GET
def ask_api(request):
    """Small JSON endpoint used by the chat widget."""
    query = _query(request)
    results = retrieve(query) if query else []
    answer, answer_note = _answer(request, query, results)
    return JsonResponse({
        "query": query,
        "answer": answer["text"] if answer else None,
        "answer_provider": answer["provider"] if answer else None,
        "answer_note": answer_note,
        "results": [
            {
                "title": r["title"],
                "kind": r["kind_label"],
                "url": r["url"],
                "snippet": r["snippet"],
                "verified": r["verified"],
                "demo": r["demo"],
            }
            for r in results
        ],
        "handoff": [t["label"] for t in detect_triggers(query)] if query else [],
    })


def knowledge_detail(request, pk):
    entry = get_object_or_404(KnowledgeEntry, pk=pk, is_published=True)
    return render(request, "core/knowledge_detail.html", {"entry": entry})
