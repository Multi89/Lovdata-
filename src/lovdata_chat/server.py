from __future__ import annotations

from typing import Literal

from mcp.server.fastmcp import FastMCP

from .answer_style import ExplanationLevel, get_style_guide
from .config import settings
from .pro_gateway import ProGateway, ProGatewayError
from .public_index import fetch as public_fetch
from .public_index import find_terms as public_find_terms
from .public_index import index_status, search as public_search


mcp = FastMCP(
    "Lovdata",
    instructions=(
        "Les-only verktøy for norske rettskilder. Bruk offentlige Lovdata-data for lover og "
        "forskrifter. Bruk Lovdata Pro-gateway bare når den er konfigurert og brukeren ber om "
        "Pro-kilder som rettsavgjørelser, forarbeider, rundskriv eller historiske versjoner. "
        "Oppgi alltid dokumenttittel, dokument-ID, URL og om kilden er Lovdata API eller Pro. "
        "Ikke presenter svar som juridisk rådgivning."
    ),
    stateless_http=True,
    json_response=True,
    host=settings.host,
    port=settings.port,
)
pro = ProGateway(settings)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
def lovdata_status() -> dict:
    """Use this when you need to check whether public Lovdata data and Lovdata Pro are ready."""
    return {
        "public_index": index_status(settings.db_path),
        "lovdata_pro": pro.status(),
        "safety": {
            "read_only": True,
            "stores_lovdata_password": False,
            "browser_cookie_automation": False,
        },
    }


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def lovdata_search(
    query: str,
    scope: Literal["auto", "public", "pro"] = "auto",
    sources: list[str] | None = None,
    limit: int = 8,
) -> dict:
    """Use this when the user wants to find Norwegian laws, regulations, cases, preparatory works, circulars, historical versions, or other Lovdata sources."""
    limit = max(1, min(limit, 20))
    public_results: list[dict] = []
    pro_results: list[dict] = []
    warnings: list[str] = []

    if scope in {"auto", "public"}:
        public_results = public_search(settings.db_path, query, sources, limit)
        if not index_status(settings.db_path)["ready"]:
            warnings.append("Offentlig indeks er ikke bygget. Indekser gjeldende lover og sentrale forskrifter.")

    if scope in {"auto", "pro"}:
        if pro.configured:
            try:
                pro_results = await pro.search(query, sources, limit)
            except (ProGatewayError, Exception) as exc:
                warnings.append(f"Lovdata Pro-søk feilet: {exc}")
        elif scope == "pro":
            warnings.append(pro.status()["message"])

    combined = pro_results + public_results
    seen: set[str] = set()
    deduped: list[dict] = []
    for item in combined:
        key = str(item.get("document_id") or item.get("url") or item.get("title"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break

    return {
        "query": query,
        "scope": scope,
        "results": deduped,
        "result_count": len(deduped),
        "warnings": warnings,
        "citation_instruction": "Siter dokumenttittel, dokument-ID og Lovdata-URL i svaret.",
    }


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def lovdata_research(
    question: str,
    explanation_level: ExplanationLevel = "lett",
    scope: Literal["auto", "public", "pro"] = "auto",
    sources: list[str] | None = None,
    limit: int = 8,
) -> dict:
    """Use this when the user asks a Norwegian legal question and wants source-backed material written at a light, normal, or professor level."""
    search_result = await lovdata_search(
        query=question,
        scope=scope,
        sources=sources,
        limit=limit,
    )
    search_result["question"] = question
    search_result["explanation_level"] = explanation_level
    search_result["style_guide"] = get_style_guide(explanation_level)
    search_result["answer_rules"] = [
        "Bruk bare rettslige påstander som kan forankres i de returnerte kildene.",
        "Oppgi dokumenttittel, dokument-ID og Lovdata-lenke for sentrale kilder.",
        "Skill mellom sikker rett, usikker tolkning og faktumavhengig vurdering.",
        "Ikke presenter svaret som bindende juridisk rådgivning.",
    ]
    return search_result


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def lovdata_fetch(
    document_id: str,
    scope: Literal["auto", "public", "pro"] = "auto",
    max_chars: int = 24_000,
) -> dict:
    """Use this when a specific Lovdata document must be read after a search result supplied its document ID or URL."""
    max_chars = max(1_000, min(max_chars, 100_000))
    if scope in {"auto", "public"}:
        item = public_fetch(settings.db_path, document_id, max_chars)
        if item is not None:
            return item

    if scope in {"auto", "pro"}:
        try:
            return await pro.fetch(document_id, max_chars)
        except ProGatewayError as exc:
            return {
                "error": str(exc),
                "document_id": document_id,
                "scope": scope,
                "lovdata_pro_home": "https://lovdata.no/",
            }

    return {"error": "Dokumentet ble ikke funnet i den offentlige indeksen.", "document_id": document_id}


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def lovdata_find_in_document(
    document_id: str,
    terms: list[str],
    scope: Literal["auto", "public", "pro"] = "auto",
    max_hits: int = 20,
) -> dict:
    """Use this when the user asks where named words, rights, duties, paragraphs, or legal concepts appear inside one Lovdata document."""
    max_hits = max(1, min(max_hits, 50))
    if scope in {"auto", "public"}:
        result = public_find_terms(settings.db_path, document_id, terms, max_hits)
        if result is not None:
            return result

    if scope in {"auto", "pro"}:
        try:
            document = await pro.fetch(document_id, 500_000)
        except ProGatewayError as exc:
            return {"error": str(exc), "document_id": document_id}
        text = document.get("text", "")
        lowered = text.lower()
        hits: list[dict] = []
        for term in terms:
            needle = term.strip().lower()
            if not needle:
                continue
            start = 0
            while len(hits) < max_hits:
                pos = lowered.find(needle, start)
                if pos < 0:
                    break
                left = max(0, pos - 280)
                right = min(len(text), pos + len(term) + 280)
                hits.append({"term": term, "position": pos, "context": text[left:right].strip()})
                start = pos + max(1, len(needle))
        return {
            "document_id": document.get("document_id", document_id),
            "title": document.get("title"),
            "url": document.get("url"),
            "hits": hits,
            "hit_count": len(hits),
            "source": "Lovdata Pro",
        }

    return {"error": "Dokumentet ble ikke funnet.", "document_id": document_id}


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
