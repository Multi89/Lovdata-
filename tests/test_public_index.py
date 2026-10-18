from pathlib import Path
import sqlite3

from lovdata_chat.public_index import fetch, find_terms, search


def make_db(path: Path) -> None:
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE documents(
            document_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            document_type TEXT NOT NULL,
            url TEXT NOT NULL,
            published_date TEXT,
            updated_date TEXT,
            body TEXT NOT NULL,
            dataset TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE documents_fts USING fts5(
            title, body, content='documents', content_rowid='rowid'
        );
        """
    )
    cur = db.execute(
        "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "LOV-2021-06-18-97",
            "Barnevernsloven",
            "lov",
            "https://lovdata.no/dokument/NL/lov/2021-06-18-97",
            "2021-06-18",
            "",
            "Barnets beste skal være et grunnleggende hensyn.",
            "test.zip",
        ),
    )
    rowid = cur.lastrowid
    db.execute(
        "INSERT INTO documents_fts(rowid, title, body) VALUES (?, ?, ?)",
        (rowid, "Barnevernsloven", "Barnets beste skal være et grunnleggende hensyn."),
    )
    db.commit()
    db.close()


def test_search_fetch_and_find(tmp_path: Path) -> None:
    db_path = tmp_path / "test.sqlite3"
    make_db(db_path)
    assert search(db_path, "barnets beste", ["lov"], 5)[0]["document_id"].startswith("LOV-")
    assert "grunnleggende" in fetch(db_path, "LOV-2021-06-18-97", 1000)["text"]
    assert find_terms(db_path, "LOV-2021-06-18-97", ["beste"], 5)["hit_count"] == 1


def test_short_law_name_prefers_the_law_over_amendments(tmp_path: Path) -> None:
    db_path = tmp_path / "test.sqlite3"
    make_db(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute(
            "UPDATE documents SET title = ? WHERE document_id = ?",
            ("Lov om barnevern (barnevernsloven)", "LOV-2021-06-18-97"),
        )
        db.execute(
            "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("LOV-2026-06-19-35", "Lov om endringer i barnevernsloven", "lov",
             "https://lovdata.no/dokument/NL/lov/2026-06-19-35", "2026-06-19", "",
             "barnevernsloven " * 30, "test.zip"),
        )
        db.execute("INSERT INTO documents_fts(documents_fts) VALUES ('rebuild')")
    results = search(db_path, "barnevernsloven", ["lov"], 5)
    assert results[0]["document_id"] == "LOV-2021-06-18-97"
