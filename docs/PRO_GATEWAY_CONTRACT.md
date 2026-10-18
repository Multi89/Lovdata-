# Lovdata Pro gateway contract

The MCP server never logs into Lovdata Pro with a username/password and never reuses a browser cookie.
`LOVDATA_PRO_GATEWAY_URL` must be an endpoint that Lovdata has approved for automated access,
or an organization-controlled gateway backed by an explicit agreement with Lovdata.

## Authentication

All requests use:

```http
Authorization: Bearer <LOVDATA_PRO_GATEWAY_TOKEN>
Accept: application/json
```

## Search

`POST /v1/search`

```json
{
  "query": "barnets beste funksjonsnedsettelse barnevern",
  "sources": ["rettsavgjørelse", "forarbeid", "rundskriv"],
  "limit": 8
}
```

Expected response:

```json
{
  "results": [
    {
      "document_id": "HR-2025-1234-A",
      "title": "Eksempelavgjørelse",
      "document_type": "rettsavgjørelse",
      "url": "https://lovdata.no/dokument/...",
      "date": "2025-06-01",
      "snippet": "Kort utdrag som avtalen tillater at klienten mottar."
    }
  ]
}
```

## Fetch one document

`GET /v1/documents/{url_encoded_document_id}`

Expected response:

```json
{
  "document_id": "HR-2025-1234-A",
  "title": "Eksempelavgjørelse",
  "document_type": "rettsavgjørelse",
  "url": "https://lovdata.no/dokument/...",
  "date": "2025-06-01",
  "text": "Dokumenttekst i det omfang avtalen med Lovdata tillater."
}
```

The gateway should enforce per-user authorization, rate limits, audit logging, content limits,
and any source restrictions in the Lovdata agreement.
