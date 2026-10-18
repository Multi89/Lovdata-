from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any


_WORD_RE = re.compile(r"[0-9A-Za-zÆØÅæøå§_-]+", re.UNICODE)


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def index_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "ready": False,
            "database": str(path),
            "documents": 0,
            "message": "Bygg indeksen med `lovdata-sync --matching gjeldende-lover --matching gjeldende-sentrale-forskrifter`.",
        }

    try:
        with _connect(path) as db:
            count = db.execute("SELECT COUNT(*) AS n FROM documents").fetchone()["n"]
            meta_rows = db.execute("SELECT key, value FROM metadata").fetchall()
        return {
            "ready": True,
            "database": str(path),
            "documents": int(count),
            "metadata": {row["key"]: row["value"] for row in meta_rows},
        }
    except sqlite3.Error as exc:
        return {
            "ready": False,
            "database": str(path),
            "documents": 0,
            "message": f"Indeksen kunne ikke leses: {exc}",
        }


def _fts_query(query: str, operator: str = "AND") -> str:
    words = _WORD_RE.findall(query)
    if not words:
        raise ValueError("Søket må inneholde minst ett ord eller paragrafnummer.")
    safe_operator = "OR" if operator.upper() == "OR" else "AND"
    return f" {safe_operator} ".join(
        f'"{word.replace(chr(34), "")}"' for word in words[:20]
    )


def search(path: Path, query: str, sources: list[str] | None, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    source_filter = [item.strip().lower() for item in (sources or []) if item.strip()]
    params: list[Any] = [_fts_query(query)]
    where = "documents_fts MATCH ?"

    if source_filter:
        placeholders = ",".join("?" for _ in source_filter)
        where += f" AND lower(d.document_type) IN ({placeholders})"
        params.extend(source_filter)

    title_query = " ".join(query.casefold().split())
    title_priority = [title_query, f"({title_query})", title_query]
    params.extend(title_priority)
    params.append(limit)
    sql = f"""
        SELECT
            d.document_id,
            d.title,
            d.document_type,
            d.url,
            d.published_date,
            d.updated_date,
            d.dataset,
            snippet(documents_fts, 1, '[', ']', ' … ', 26) AS snippet,
            bm25(documents_fts, 4.0, 1.0) AS rank
        FROM documents_fts
        JOIN documents d ON d.rowid = documents_fts.rowid
        WHERE {where}
        ORDER BY
            CASE
                WHEN lower(d.title) = ? OR instr(lower(d.title), ?) > 0 THEN 0
                WHEN instr(lower(d.title), ?) > 0 THEN 1
                ELSE 2
            END,
            rank
        LIMIT ?
    """

    with _connect(path) as db:
        try:
            rows = db.execute(sql, params).fetchall()
            # Hvis alle ordene samlet blir for strengt, gjør et bredere OR-søk.
            if not rows and len(_WORD_RE.findall(query)) > 1:
                broad_params: list[Any] = [_fts_query(query, "OR")]
                if source_filter:
                    broad_params.extend(source_filter)
                broad_params.extend(title_priority)
                broad_params.append(limit)
                rows = db.execute(sql, broad_params).fetchall()
        except sqlite3.OperationalError:
            # Fallback for Python builds without FTS5.
            words = _WORD_RE.findall(query)
            clauses = []
            fallback_params: list[Any] = []
            for word in words[:20]:
                like = f"%{word}%"
                clauses.append("(d.title LIKE ? OR d.body LIKE ?)")
                fallback_params.extend([like, like])
            fallback_where = " AND ".join(clauses) or "1=0"
            if source_filter:
                placeholders = ",".join("?" for _ in source_filter)
                fallback_where += f" AND lower(d.document_type) IN ({placeholders})"
                fallback_params.extend(source_filter)
            fallback_params.append(limit)
            rows = db.execute(
                f"""
                SELECT d.document_id, d.title, d.document_type, d.url,
                       d.published_date, d.updated_date, d.dataset,
                       substr(d.body, 1, 600) AS snippet, 0 AS rank
                FROM documents d
                WHERE {fallback_where}
                ORDER BY d.title
                LIMIT ?
                """,
                fallback_params,
            ).fetchall()

    return [
        {
            "document_id": row["document_id"],
            "title": row["title"],
            "document_type": row["document_type"],
            "url": row["url"],
            "published_date": row["published_date"],
            "updated_date": row["updated_date"],
            "snippet": row["snippet"],
            "source": "Lovdata API",
            "dataset": row["dataset"],
            "license": "NLOD 2.0",
        }
        for row in rows
    ]


def fetch(path: Path, document_id: str, max_chars: int) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with _connect(path) as db:
        row = db.execute(
            """
            SELECT document_id, title, document_type, url, published_date,
                   updated_date, body, dataset
            FROM documents
            WHERE document_id = ? OR url = ?
            LIMIT 1
            """,
            (document_id, document_id),
        ).fetchone()
    if row is None:
        return None

    body = row["body"] or ""
    truncated = len(body) > max_chars
    return {
        "document_id": row["document_id"],
        "title": row["title"],
        "document_type": row["document_type"],
        "url": row["url"],
        "published_date": row["published_date"],
        "updated_date": row["updated_date"],
        "text": body[:max_chars],
        "truncated": truncated,
        "source": "Lovdata API",
        "dataset": row["dataset"],
        "license": "NLOD 2.0",
    }


def find_terms(
    path: Path,
    document_id: str,
    terms: list[str],
    max_hits: int,
    context_chars: int = 280,
) -> dict[str, Any] | None:
    document = fetch(path, document_id, max_chars=2_000_000)
    if document is None:
        return None

    text = document["text"]
    lowered = text.lower()
    hits: list[dict[str, Any]] = []
    for term in terms:
        needle = term.strip().lower()
        if not needle:
            continue
        start = 0
        while len(hits) < max_hits:
            pos = lowered.find(needle, start)
            if pos < 0:
                break
            left = max(0, pos - context_chars)
            right = min(len(text), pos + len(term) + context_chars)
            hits.append(
                {
                    "term": term,
                    "position": pos,
                    "context": text[left:right].strip(),
                }
            )
            start = pos + max(1, len(needle))
        if len(hits) >= max_hits:
            break

    return {
        "document_id": document["document_id"],
        "title": document["title"],
        "url": document["url"],
        "hits": hits,
        "hit_count": len(hits),
        "source": document["source"],
    }
