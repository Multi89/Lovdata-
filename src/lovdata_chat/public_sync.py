from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import urllib.request
import zipfile
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

from .config import settings


ARCHIVE_RE = re.compile(
    r"[^/\\\"']+\.(?:zip|tar\.bz2|tar\.gz|tgz)$", re.IGNORECASE
)
FILENAME_ID_RE = re.compile(
    r"(?:^|/)(nl|sf|lf|lti)[-_](\d{4})(\d{2})(\d{2})[-_](\d+)",
    re.IGNORECASE,
)
LEGAL_ID_RE = re.compile(
    r"\b(?:LOV|FOR|RES|INS|DEL|STV|LTI)-\d{4}-\d{2}-\d{2}-\d+[A-Za-z]?\b",
    re.IGNORECASE,
)
TITLE_TAGS = {
    "title",
    "tittel",
    "korttittel",
    "shorttitle",
    "dokumenttittel",
    "heading",
    "overskrift",
}
DATE_TAGS = {"dato", "date", "published", "publisert", "kunngjort"}
UPDATED_TAGS = {"sistendret", "updated", "endret", "lastmodified"}
URL_TAGS = {"url", "uri", "href", "link"}


def _request_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "lovdata-chat-mcp/0.1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def _collect_archive_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, str):
        match = ARCHIVE_RE.search(value)
        if match:
            names.add(match.group(0))
    elif isinstance(value, list):
        for item in value:
            names.update(_collect_archive_names(item))
    elif isinstance(value, dict):
        for item in value.values():
            names.update(_collect_archive_names(item))
    return names


def list_datasets(base_url: str) -> list[str]:
    data = _request_json(f"{base_url.rstrip('/')}/v1/publicData/list")
    return sorted(_collect_archive_names(data))


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "lovdata-chat-mcp/0.1.0"})
    with urllib.request.urlopen(request, timeout=300) as response, destination.open("wb") as out:
        while chunk := response.read(1024 * 1024):
            out.write(chunk)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower().replace("-", "").replace("_", "")


def _first_text(root: ET.Element, candidates: set[str]) -> str | None:
    for elem in root.iter():
        if _local_name(elem.tag) in candidates and elem.text and elem.text.strip():
            return " ".join(elem.text.split())
    return None


def _metadata_text(root: ET.Element, field: str) -> str | None:
    for elem in root.iter():
        if _local_name(elem.tag) == "dd" and field in elem.get("class", "").split():
            value = " ".join(" ".join(elem.itertext()).split())
            if value:
                return value
    return None


def _extract_text(root: ET.Element) -> str:
    parts: list[str] = []
    for text in root.itertext():
        cleaned = " ".join(text.split())
        if cleaned:
            parts.append(cleaned)
    return "\n".join(parts)


def _document_type(document_id: str, filename: str, title: str) -> str:
    upper = document_id.upper()
    if upper.startswith("LOV-"):
        return "lov"
    if upper.startswith("FOR-"):
        return "forskrift"
    if upper.startswith("LTI-"):
        return "norsk_lovtidend"
    if upper.startswith("RES-"):
        return "resolusjon"
    if upper.startswith("INS-"):
        return "instruks"
    if upper.startswith("DEL-"):
        return "delegering"
    combined = f"{filename} {title}".lower()
    if "forskrift" in combined:
        return "forskrift"
    if "lov" in combined:
        return "lov"
    return "annet"


def _lovdata_url(document_id: str) -> str:
    upper = document_id.upper()
    value = document_id
    if upper.startswith("LOV-"):
        return f"https://lovdata.no/dokument/NL/lov/{value[4:]}"
    if upper.startswith("FOR-"):
        return f"https://lovdata.no/dokument/SF/forskrift/{value[4:]}"
    if upper.startswith("LTI-"):
        return f"https://lovdata.no/dokument/LTI/{value[4:]}"
    return "https://lovdata.no/"


def _document_id_from_filename(filename: str) -> str | None:
    match = FILENAME_ID_RE.search(filename.replace("\\", "/"))
    if not match:
        return None
    kind, year, month, day, number = match.groups()
    prefix = {"nl": "LOV", "sf": "FOR", "lf": "FOR", "lti": "LTI"}[kind.lower()]
    normalized_number = str(int(number))
    return f"{prefix}-{year}-{month}-{day}-{normalized_number}"


def _parse_xml(content: bytes, filename: str, dataset: str) -> dict[str, str] | None:
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return None

    body = _extract_text(root)
    if not body:
        return None

    document_id = _metadata_text(root, "legacyID") or _document_id_from_filename(filename)
    if not document_id:
        id_match = LEGAL_ID_RE.search(filename) or LEGAL_ID_RE.search(body)
        document_id = id_match.group(0) if id_match else ""
    document_id = document_id.upper()
    if not document_id:
        digest = hashlib.sha256(content).hexdigest()[:20]
        document_id = f"XML-{digest}"

    title = _first_text(root, TITLE_TAGS) or body.splitlines()[0][:300] or filename
    published = _metadata_text(root, "date") or _first_text(root, DATE_TAGS)
    updated = _metadata_text(root, "lastupdated") or _first_text(root, UPDATED_TAGS)
    source_path = _metadata_text(root, "dokid")
    url = (
        f"https://lovdata.no/dokument/{source_path}"
        if source_path and re.fullmatch(r"[A-Za-z0-9/_-]+", source_path)
        else _first_text(root, URL_TAGS)
    )
    if not url or not url.startswith("https://lovdata.no/"):
        url = _lovdata_url(document_id)

    return {
        "document_id": document_id,
        "title": title[:500],
        "document_type": _document_type(document_id, filename, title),
        "url": url,
        "published_date": published or "",
        "updated_date": updated or "",
        "body": body,
        "dataset": dataset,
    }


def _create_schema(db: sqlite3.Connection) -> bool:
    db.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE documents (
            document_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            document_type TEXT NOT NULL,
            url TEXT NOT NULL,
            published_date TEXT,
            updated_date TEXT,
            body TEXT NOT NULL,
            dataset TEXT NOT NULL
        );
        CREATE INDEX idx_documents_type ON documents(document_type);
        CREATE INDEX idx_documents_title ON documents(title);
        """
    )
    try:
        db.execute(
            "CREATE VIRTUAL TABLE documents_fts USING fts5(title, body, content='documents', content_rowid='rowid')"
        )
        return True
    except sqlite3.OperationalError:
        return False


def _iter_documents(archive_path: Path, dataset: str) -> Iterable[dict[str, str]]:
    lower_name = archive_path.name.lower()
    if lower_name.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                if member.is_dir() or not member.filename.lower().endswith(".xml"):
                    continue
                with archive.open(member) as source:
                    item = _parse_xml(source.read(), member.filename, dataset)
                if item:
                    yield item
        return

    if lower_name.endswith((".tar.bz2", ".tar.gz", ".tgz")):
        with tarfile.open(archive_path, mode="r:*") as archive:
            for member in archive.getmembers():
                if not member.isfile() or not member.name.lower().endswith(".xml"):
                    continue
                source = archive.extractfile(member)
                if source is None:
                    continue
                with source:
                    item = _parse_xml(source.read(), member.name, dataset)
                if item:
                    yield item
        return

    raise ValueError(f"Ustøttet Lovdata-arkivformat: {archive_path.name}")


def build_index(base_url: str, datasets: list[str], db_path: Path) -> dict[str, Any]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lovdata-sync-", dir=db_path.parent) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        temp_db = temp_dir / "lovdata.sqlite3"
        db = sqlite3.connect(temp_db)
        fts_enabled = _create_schema(db)
        total = 0
        per_dataset: dict[str, int] = {}

        for dataset in datasets:
            print(f"Laster ned {dataset} …", file=sys.stderr)
            zip_path = temp_dir / dataset
            url = f"{base_url.rstrip('/')}/v1/publicData/get/{dataset}"
            _download(url, zip_path)
            count = 0
            for item in _iter_documents(zip_path, dataset):
                cursor = db.execute(
                    """
                    INSERT INTO documents(
                        document_id, title, document_type, url,
                        published_date, updated_date, body, dataset
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(document_id) DO UPDATE SET
                        title=excluded.title,
                        document_type=excluded.document_type,
                        url=excluded.url,
                        published_date=excluded.published_date,
                        updated_date=excluded.updated_date,
                        body=excluded.body,
                        dataset=excluded.dataset
                    RETURNING rowid
                    """,
                    (
                        item["document_id"],
                        item["title"],
                        item["document_type"],
                        item["url"],
                        item["published_date"],
                        item["updated_date"],
                        item["body"],
                        item["dataset"],
                    ),
                )
                cursor.fetchone()
                count += 1
                total += 1
                if total % 500 == 0:
                    db.commit()
                    print(f"Indeksert {total} dokumenter …", file=sys.stderr)
            per_dataset[dataset] = count
            db.commit()

        if fts_enabled:
            db.execute("INSERT INTO documents_fts(documents_fts) VALUES ('rebuild')")
        document_count = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        metadata = {
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "api_base_url": base_url,
            "datasets": json.dumps(datasets, ensure_ascii=False),
            "documents": str(document_count),
            "fts5": str(fts_enabled).lower(),
            "license": "NLOD 2.0",
        }
        db.executemany("INSERT INTO metadata(key, value) VALUES (?, ?)", metadata.items())
        db.commit()
        db.close()
        os.replace(temp_db, db_path)

    return {"documents": document_count, "datasets": per_dataset, "database": str(db_path)}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Last ned og indekser Lovdatas offentlige API-datasett."
    )
    parser.add_argument("--list", action="store_true", help="Vis tilgjengelige arkivdatasett.")
    parser.add_argument("--all", action="store_true", help="Indekser alle tilgjengelige datasett.")
    parser.add_argument(
        "--dataset", action="append", default=[], help="Indekser et bestemt arkivdatasett."
    )
    parser.add_argument(
        "--matching",
        action="append",
        default=[],
        help="Indekser alle datasett der filnavnet inneholder teksten.",
    )
    parser.add_argument("--db", type=Path, default=settings.db_path)
    parser.add_argument("--base-url", default=settings.public_api_base_url)
    args = parser.parse_args()

    available = list_datasets(args.base_url)
    if args.list:
        print("\n".join(available))
        return

    selected = list(available if args.all else args.dataset)
    for pattern in args.matching:
        selected.extend(name for name in available if pattern.lower() in name.lower())
    selected = sorted(set(selected))
    unknown = sorted(set(selected) - set(available))
    if unknown:
        parser.error(f"Ukjente datasett: {', '.join(unknown)}")
    if not selected:
        parser.error(
            "Velg --all, minst ett --dataset eller minst ett --matching. Bruk --list for å se navn."
        )

    result = build_index(args.base_url, selected, args.db.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
