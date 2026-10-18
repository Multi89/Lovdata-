from __future__ import annotations

import secrets
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

from .answer_style import ExplanationLevel, get_style_guide
from .config import settings
from .pro_gateway import ProGateway, ProGatewayError
from .public_index import fetch as public_fetch
from .public_index import find_terms as public_find_terms
from .public_index import index_status, search as public_search


pro = ProGateway(settings)


class ResearchRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    explanation_level: ExplanationLevel = "lett"
    scope: Literal["auto", "public", "pro"] = "auto"
    sources: list[str] | None = None
    limit: int = Field(default=8, ge=1, le=20)


class DocumentRequest(BaseModel):
    document_id: str = Field(min_length=3, max_length=1000)
    explanation_level: ExplanationLevel = "lett"
    scope: Literal["auto", "public", "pro"] = "auto"
    max_chars: int = Field(default=24000, ge=1000, le=100000)


class FindRequest(BaseModel):
    document_id: str = Field(min_length=3, max_length=1000)
    terms: list[str] = Field(min_length=1, max_length=20)
    explanation_level: ExplanationLevel = "lett"
    scope: Literal["auto", "public", "pro"] = "auto"
    max_hits: int = Field(default=20, ge=1, le=50)


def _verify_api_key(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    expected = settings.actions_api_key
    if not expected:
        return
    supplied = authorization or ""
    wanted = f"Bearer {expected}"
    if not secrets.compare_digest(supplied, wanted):
        raise HTTPException(status_code=401, detail="Ugyldig eller manglende API-nøkkel.")


Auth = Annotated[None, Depends(_verify_api_key)]


async def _combined_search(
    query: str,
    scope: Literal["auto", "public", "pro"],
    sources: list[str] | None,
    limit: int,
) -> tuple[list[dict], list[str]]:
    public_results: list[dict] = []
    pro_results: list[dict] = []
    warnings: list[str] = []

    if scope in {"auto", "public"}:
        public_results = public_search(settings.db_path, query, sources, limit)
        if not index_status(settings.db_path)["ready"]:
            warnings.append("Den offentlige Lovdata-indeksen er ikke bygget ennå.")

    if scope in {"auto", "pro"}:
        if pro.configured:
            try:
                pro_results = await pro.search(query, sources, limit)
            except (ProGatewayError, Exception) as exc:
                warnings.append(f"Lovdata Pro-søket feilet: {exc}")
        elif scope == "pro":
            warnings.append(pro.status()["message"])

    combined = pro_results + public_results
    seen: set[str] = set()
    results: list[dict] = []
    for item in combined:
        key = str(item.get("document_id") or item.get("url") or item.get("title"))
        if not key or key in seen:
            continue
        seen.add(key)
        results.append(item)
        if len(results) >= limit:
            break
    return results, warnings


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Indeksen bygges av entrypoint før serveren starter. Her unngår vi tunge
    # nettverksjobber inne i API-prosessen.
    yield


app = FastAPI(
    title="Norsk lovhjelp API",
    version="0.3.0",
    description=(
        "Read-only API for norske lover, forskrifter og andre Lovdata-kilder. "
        "Laget for en egendefinert GPT som kan forklare på lett, vanlig eller professor-nivå."
    ),
    lifespan=lifespan,
)


@app.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def privacy_policy() -> str:
    return """
    <html lang="nb"><head><title>Personvern – Norsk lovhjelp</title></head><body>
    <h1>Personvern</h1>
    <p>Norsk lovhjelp er et uoffisielt, lese-only søkeverktøy for norske rettskilder.</p>
    <p>Tjenesten trenger ikke Lovdata-passord. Søkespørsmål behandles for å finne relevante
    rettskilder. Ikke skriv fødselsnummer, passord, helseopplysninger eller andre unødvendige
    personopplysninger i spørsmålet.</p>
    <p>Lovdata Pro brukes bare gjennom en særskilt, godkjent integrasjon. Kildetekst lagres ikke
    utover det som er nødvendig for den lokale offentlige søkeindeksen.</p>
    </body></html>
    """


@app.get("/terms", response_class=HTMLResponse, include_in_schema=False)
async def terms_of_use() -> str:
    return """
    <html lang="nb"><head><title>Vilkår – Norsk lovhjelp</title></head><body>
    <h1>Vilkår</h1>
    <p>Tjenesten hjelper med å finne og forklare norske rettskilder, men gir ikke bindende
    juridisk rådgivning. Brukeren må kontrollere originalkilden og gjeldende dato.</p>
    <p>Lovdata og Lovdata Pro tilhører Stiftelsen Lovdata. Denne tjenesten er uoffisiell og må
    ikke fremstilles som godkjent av Lovdata uten skriftlig tillatelse.</p>
    </body></html>
    """


@app.get("/support", response_class=HTMLResponse, include_in_schema=False)
async def support_page() -> str:
    return """
    <html lang="nb"><head><title>Hjelp – Norsk lovhjelp</title></head><body>
    <h1>Hjelp</h1>
    <p>Prøv: «Finn reglene om journalinnsyn i barnevernet og forklar lett.»</p>
    <p>Du kan velge nivå: lett, vanlig eller professor.</p>
    </body></html>
    """


@app.get("/healthz", include_in_schema=False)
async def liveness() -> dict:
    return {"status": "ok"}


@app.get("/health", operation_id="checkLovdataStatus", tags=["status"])
async def health(_: Auth) -> dict:
    return {
        "status": "ok",
        "public_index": index_status(settings.db_path),
        "lovdata_pro": pro.status(),
        "read_only": True,
        "supported_explanation_levels": ["lett", "vanlig", "professor"],
    }


@app.post("/api/research", operation_id="researchNorwegianLaw", tags=["law"])
async def research_law(request: ResearchRequest, _: Auth) -> dict:
    try:
        results, warnings = await _combined_search(
            request.question,
            request.scope,
            request.sources,
            request.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "question": request.question,
        "explanation_level": request.explanation_level,
        "style_guide": get_style_guide(request.explanation_level),
        "results": results,
        "result_count": len(results),
        "warnings": warnings,
        "answer_rules": [
            "Bruk bare rettslige påstander som kan forankres i de returnerte kildene.",
            "Oppgi dokumenttittel, dokument-ID og Lovdata-lenke for hver sentral kilde.",
            "Kontroller at kilden gjelder den tidsperioden brukeren spør om.",
            "Opplys tydelig når Lovdata Pro-kilder ikke var tilgjengelige.",
            "Ikke presenter svaret som bindende juridisk rådgivning.",
        ],
    }


@app.post("/api/document", operation_id="readNorwegianLegalDocument", tags=["law"])
async def read_document(request: DocumentRequest, _: Auth) -> dict:
    if request.scope in {"auto", "public"}:
        item = public_fetch(settings.db_path, request.document_id, request.max_chars)
        if item is not None:
            item["style_guide"] = get_style_guide(request.explanation_level)
            return item

    if request.scope in {"auto", "pro"}:
        try:
            item = await pro.fetch(request.document_id, request.max_chars)
            item["style_guide"] = get_style_guide(request.explanation_level)
            return item
        except ProGatewayError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    raise HTTPException(status_code=404, detail="Dokumentet ble ikke funnet.")


@app.post("/api/find", operation_id="findTermsInNorwegianLegalDocument", tags=["law"])
async def find_in_document(request: FindRequest, _: Auth) -> dict:
    if request.scope in {"auto", "public"}:
        result = public_find_terms(
            settings.db_path,
            request.document_id,
            request.terms,
            request.max_hits,
        )
        if result is not None:
            result["style_guide"] = get_style_guide(request.explanation_level)
            return result

    if request.scope in {"auto", "pro"}:
        try:
            document = await pro.fetch(request.document_id, 500000)
        except ProGatewayError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        text = str(document.get("text") or "")
        lowered = text.lower()
        hits: list[dict] = []
        for term in request.terms:
            needle = term.strip().lower()
            if not needle:
                continue
            start = 0
            while len(hits) < request.max_hits:
                position = lowered.find(needle, start)
                if position < 0:
                    break
                left = max(0, position - 280)
                right = min(len(text), position + len(term) + 280)
                hits.append(
                    {
                        "term": term,
                        "position": position,
                        "context": text[left:right].strip(),
                    }
                )
                start = position + max(1, len(needle))
        return {
            "document_id": document.get("document_id", request.document_id),
            "title": document.get("title"),
            "url": document.get("url"),
            "source": "Lovdata Pro",
            "hits": hits,
            "hit_count": len(hits),
            "style_guide": get_style_guide(request.explanation_level),
        }

    raise HTTPException(status_code=404, detail="Dokumentet ble ikke funnet.")


def main() -> None:
    uvicorn.run(
        "lovdata_chat.actions_api:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
