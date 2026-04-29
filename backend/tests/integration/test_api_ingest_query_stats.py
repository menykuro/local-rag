"""Pruebas de integracion para endpoints de ingesta, query y stats."""

from io import BytesIO


def test_root_and_stats_smoke(client, rag_instance):
    rag_instance.stats = {"doc_count": 3, "chunk_count": 8, "index_size": "12KB"}

    root_resp = client.get("/")
    assert root_resp.status_code == 200
    assert "message" in root_resp.json()

    stats_resp = client.get("/api/stats")
    assert stats_resp.status_code == 200
    assert stats_resp.json()["doc_count"] == 3


def test_ingest_uses_stable_upload_source(client, monkeypatch, rag_instance):
    from app.api import ingest as ingest_api

    captured = {}

    def fake_process_file(path, source=None):
        captured["source"] = source
        rag_instance.add_documents(["chunk-1", "chunk-2"], source)
        return {"filename": "README.md", "chunks": 2}

    monkeypatch.setattr(ingest_api, "process_file", fake_process_file)

    files = {"files": ("README.md", BytesIO(b"contenido"), "text/markdown")}
    response = client.post("/api/ingest", files=files)
    assert response.status_code == 200
    assert captured["source"] == "upload::README.md"
    assert response.json()["indexed_chunks"] == 2


def test_query_with_relevant_results_returns_sources(client, rag_instance):
    rag_instance.search_results = (
        [{"source": "docA.md", "text": "contexto A"}],
        [0.91],
    )
    rag_instance.answer_text = "respuesta local"

    response = client.post("/api/query", json={"query": "Que dice A?"})
    assert response.status_code == 200
    body = response.json()
    assert body["used_web"] is False
    assert "docA.md" in body["sources"]
    assert "respuesta local" in body["answer"]


def test_query_fallback_without_web(client, rag_instance, monkeypatch):
    from app.api import query as query_api

    rag_instance.search_results = ([], [])
    monkeypatch.setattr(query_api.settings, "enable_web_fallback", False)
    rag_instance.answer_text = "sin web"

    response = client.post("/api/query", json={"query": "dato realtime"})
    assert response.status_code == 200
    body = response.json()
    assert body["used_web"] is False
    assert "Base de Conocimiento Interna (LLM)" in body["sources"][0]


def test_query_fallback_with_web(client, rag_instance, monkeypatch):
    from app.api import query as query_api
    import app.core.web_search as web_search

    rag_instance.search_results = ([], [])
    rag_instance.answer_text = "con web"
    monkeypatch.setattr(query_api.settings, "enable_web_fallback", True)
    monkeypatch.setattr(
        web_search,
        "perform_web_search",
        lambda q: ("contexto web", ["https://example.com"]),
    )

    response = client.post("/api/query", json={"query": "ultima noticia"})
    assert response.status_code == 200
    body = response.json()
    assert body["used_web"] is True
    assert body["sources"] == ["https://example.com"]
    assert body["answer"] == "con web"
