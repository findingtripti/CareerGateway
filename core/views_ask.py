"""Ask Career Gateway: answers come only from stored records (PDF section 13)."""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .handoff import SUGGESTED_MESSAGE, detect_triggers
from .models import KnowledgeEntry
from .retrieval import retrieve

QUERY_LIMIT = 200


def _query(request):
    return request.GET.get("q", "").strip()[:QUERY_LIMIT]


@require_GET
def ask(request):
    query = _query(request)
    results = retrieve(query) if query else []
    return render(request, "core/ask.html", {
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
    return JsonResponse({
        "query": query,
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
