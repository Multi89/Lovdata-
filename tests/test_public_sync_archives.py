from io import BytesIO
from pathlib import Path
import tarfile

from lovdata_chat.public_sync import (
    _collect_archive_names,
    _document_id_from_filename,
    _iter_documents,
    _parse_xml,
    build_index,
)
from lovdata_chat import public_sync
from lovdata_chat.public_index import fetch, search


def test_collects_zip_and_tar_archives() -> None:
    data = {
        "files": [
            "gjeldende-lover.tar.bz2",
            "gjeldende-sentrale-forskrifter.tar.gz",
            "lti-2026.zip",
        ]
    }
    assert _collect_archive_names(data) == {
        "gjeldende-lover.tar.bz2",
        "gjeldende-sentrale-forskrifter.tar.gz",
        "lti-2026.zip",
    }


def test_reads_xml_from_tar_bz2(tmp_path: Path) -> None:
    archive_path = tmp_path / "gjeldende-lover.tar.bz2"
    content = b"""<?xml version='1.0' encoding='utf-8'?>
    <document><title>Testloven</title><id>LOV-2024-01-01-1</id>
    <body>Dette er en norsk lov.</body></document>"""

    with tarfile.open(archive_path, "w:bz2") as archive:
        info = tarfile.TarInfo("nl/LOV-2024-01-01-1.xml")
        info.size = len(content)
        archive.addfile(info, BytesIO(content))

    documents = list(_iter_documents(archive_path, archive_path.name))
    assert len(documents) == 1
    assert documents[0]["document_id"] == "LOV-2024-01-01-1"
    assert documents[0]["document_type"] == "lov"


def test_document_id_from_lovdata_filenames() -> None:
    assert _document_id_from_filename("nl/nl-18840614-003.xml") == "LOV-1884-06-14-3"
    assert _document_id_from_filename("sf/sf-20240102-0042.xml") == "FOR-2024-01-02-42"


def test_header_identity_wins_over_referenced_law() -> None:
    content = b'''<html><head><title>Norske Lov</title></head><body>
    <dd class="legacyID">LOV-1687-04-15</dd>
    <dd class="dokid">NL/lov/1687-04-15</dd>
    <p>Endret ved LOV-2023-06-16-40.</p></body></html>'''
    document = _parse_xml(content, "nl/nl-16870415-000.xml", "test.tar.bz2")
    assert document["document_id"] == "LOV-1687-04-15"
    assert document["url"] == "https://lovdata.no/dokument/NL/lov/1687-04-15"


def test_filename_identity_wins_over_referenced_law() -> None:
    content = b'<document><title>Test</title><body>Se LOV-2021-06-18-97.</body></document>'
    document = _parse_xml(content, "nl/nl-20060519-016.xml", "test.tar.bz2")
    assert document["document_id"] == "LOV-2006-05-19-16"


def test_build_index_rebuilds_search_after_duplicate_document(tmp_path, monkeypatch) -> None:
    versions = {
        "first.tar.bz2": b'<document><title>Testloven</title><body>gammelversjon</body></document>',
        "second.tar.bz2": b'<document><title>Testloven</title><body>nyversjon</body></document>',
    }

    def download(url, destination):
        content = versions[url.rsplit("/", 1)[-1]]
        with tarfile.open(destination, "w:bz2") as archive:
            info = tarfile.TarInfo("nl/nl-20060519-016.xml")
            info.size = len(content)
            archive.addfile(info, BytesIO(content))

    monkeypatch.setattr(public_sync, "_download", download)
    db_path = tmp_path / "index.sqlite3"
    result = build_index("https://api.lovdata.no", list(versions), db_path)
    assert result["documents"] == 1
    assert fetch(db_path, "LOV-2006-05-19-16", 1000)["text"].endswith("nyversjon")
    assert search(db_path, "nyversjon", None, 5)[0]["document_id"] == "LOV-2006-05-19-16"
    assert search(db_path, "gammelversjon", None, 5) == []
