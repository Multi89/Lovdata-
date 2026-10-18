from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from .config import Settings


class ProGatewayError(RuntimeError):
    pass


class ProGateway:
    """Client for an approved Lovdata Pro API/gateway.

    This class deliberately does not implement browser automation, password login,
    cookie reuse, scraping, mass download, or reverse-engineered private endpoints.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(self.settings.pro_gateway_url and self.settings.pro_gateway_token)

    def status(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "gateway_url": self.settings.pro_gateway_url or None,
            "authentication": "Bearer token" if self.configured else None,
            "message": (
                "Lovdata Pro-gateway er konfigurert."
                if self.configured
                else "Pro-verktøyene venter på et API/gateway-endepunkt godkjent av Lovdata."
            ),
        }

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise ProGatewayError(
                "Lovdata Pro er ikke aktivert. Sett LOVDATA_PRO_GATEWAY_URL og "
                "LOVDATA_PRO_GATEWAY_TOKEN etter at Lovdata har godkjent integrasjonen. "
                "Ikke bruk brukernavn, passord eller nettleser-cookie."
            )
        return {
            "Authorization": f"Bearer {self.settings.pro_gateway_token}",
            "Accept": "application/json",
            "User-Agent": "lovdata-chat-mcp/0.1.0",
        }

    async def search(
        self, query: str, sources: list[str] | None, limit: int
    ) -> list[dict[str, Any]]:
        url = f"{self.settings.pro_gateway_url}{self.settings.pro_search_path}"
        payload = {"query": query, "sources": sources or [], "limit": limit}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self._headers(), json=payload)
        if response.status_code == 401:
            raise ProGatewayError("Pro-gatewayen avviste tilgangstokenet (401).")
        response.raise_for_status()
        data = response.json()
        raw_results = data.get("results", data) if isinstance(data, dict) else data
        if not isinstance(raw_results, list):
            raise ProGatewayError("Pro-gatewayen returnerte et ukjent svarformat.")

        results: list[dict[str, Any]] = []
        for item in raw_results[:limit]:
            if not isinstance(item, dict):
                continue
            results.append(
                {
                    "document_id": str(item.get("document_id") or item.get("id") or ""),
                    "title": str(item.get("title") or "Uten tittel"),
                    "document_type": item.get("document_type") or item.get("source_type"),
                    "url": item.get("url"),
                    "date": item.get("date") or item.get("published_date"),
                    "snippet": item.get("snippet") or item.get("summary"),
                    "source": "Lovdata Pro",
                }
            )
        return results

    async def fetch(self, document_id: str, max_chars: int) -> dict[str, Any]:
        path = self.settings.pro_document_path.format(
            document_id=quote(document_id, safe="")
        )
        url = f"{self.settings.pro_gateway_url}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._headers())
        if response.status_code == 404:
            raise ProGatewayError("Dokumentet ble ikke funnet i Pro-gatewayen.")
        if response.status_code == 401:
            raise ProGatewayError("Pro-gatewayen avviste tilgangstokenet (401).")
        response.raise_for_status()
        item = response.json()
        if not isinstance(item, dict):
            raise ProGatewayError("Pro-gatewayen returnerte et ukjent dokumentformat.")
        text = str(item.get("text") or item.get("body") or "")
        return {
            "document_id": str(item.get("document_id") or item.get("id") or document_id),
            "title": str(item.get("title") or "Uten tittel"),
            "document_type": item.get("document_type") or item.get("source_type"),
            "url": item.get("url"),
            "date": item.get("date") or item.get("published_date"),
            "text": text[:max_chars],
            "truncated": len(text) > max_chars,
            "source": "Lovdata Pro",
        }
