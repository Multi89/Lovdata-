from fastapi.testclient import TestClient
from dataclasses import replace

from lovdata_chat.actions_api import app
from lovdata_chat import actions_api
from test_public_index import make_db


def test_health_and_openapi() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["supported_explanation_levels"] == [
        "lett",
        "vanlig",
        "professor",
    ]

    schema = client.get("/openapi.json").json()
    operation_ids = {
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }
    assert "researchNorwegianLaw" in operation_ids
    assert "readNorwegianLegalDocument" in operation_ids
    assert "findTermsInNorwegianLegalDocument" in operation_ids


def test_hosting_healthcheck_does_not_require_api_key(monkeypatch) -> None:
    monkeypatch.setattr(
        actions_api,
        "settings",
        replace(actions_api.settings, actions_api_key="test-healthcheck-key"),
    )
    client = TestClient(app)
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/health").status_code == 401
    assert client.post(
        "/api/research", json={"question": "barnets beste"}
    ).status_code == 401
    assert client.get(
        "/health", headers={"Authorization": "Bearer test-healthcheck-key"}
    ).status_code == 200


def test_research_document_and_find_work_together(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "index.sqlite3"
    make_db(db_path)
    monkeypatch.setattr(actions_api, "settings", replace(actions_api.settings, db_path=db_path))
    client = TestClient(app)
    research = client.post("/api/research", json={
        "question": "barnets beste", "scope": "public", "explanation_level": "professor"
    })
    assert research.status_code == 200
    document_id = research.json()["results"][0]["document_id"]
    assert research.json()["style_guide"]["level"] == "professor"
    document = client.post("/api/document", json={"document_id": document_id, "scope": "public"})
    assert document.status_code == 200
    assert "grunnleggende" in document.json()["text"]
    found = client.post("/api/find", json={
        "document_id": document_id, "terms": ["beste"], "scope": "public"
    })
    assert found.status_code == 200
    assert found.json()["hit_count"] == 1


def test_invalid_search_and_missing_document_are_reported(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "index.sqlite3"
    make_db(db_path)
    monkeypatch.setattr(actions_api, "settings", replace(actions_api.settings, db_path=db_path))
    client = TestClient(app)
    assert client.post("/api/research", json={"question": "!!", "scope": "public"}).status_code == 400
    assert client.post("/api/research", json={"question": "x"}).status_code == 422
    assert client.post("/api/document", json={
        "document_id": "LOV-1900-01-01-999", "scope": "public"
    }).status_code == 404
