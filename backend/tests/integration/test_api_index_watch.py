"""Pruebas de integracion de gestion de indice y ciclo de watch folders."""

import json


def test_watch_status_returns_configured_paths(client, temp_runtime_settings):
    temp_runtime_settings.write_text(
        json.dumps(
            {
                "watch_folders": [
                    {"path": "C:\\docs\\a", "active": True, "recursive": True},
                    {"path": "C:\\docs\\b", "active": False, "recursive": True},
                ]
            }
        ),
        encoding="utf-8",
    )

    response = client.get("/api/index/watch/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    assert len(data["folders"]) == 2
    assert data["running"] is False


def test_watch_lifecycle_start_pause_resume_and_all_toggles(client):
    start_resp = client.post("/api/index/watch/start", json={"path": "C:\\docs\\tfm", "recursive": True})
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "started"

    pause_resp = client.post("/api/index/watch/pause", json={"path": "C:\\docs\\tfm"})
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "paused"

    resume_resp = client.post("/api/index/watch/resume", json={"path": "C:\\docs\\tfm"})
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "resumed"

    pause_all = client.post("/api/index/watch/pause-all")
    assert pause_all.status_code == 200
    assert pause_all.json()["status"] == "paused_all"

    resume_all = client.post("/api/index/watch/resume-all")
    assert resume_all.status_code == 200
    assert resume_all.json()["status"] == "resumed_all"


def test_watch_start_returns_400_when_path_is_not_directory(client, monkeypatch):
    from app.api import index as index_api

    monkeypatch.setattr(index_api.os.path, "isdir", lambda p: False)
    response = client.post("/api/index/watch/start", json={"path": "C:\\does-not-exist"})
    assert response.status_code == 400


def test_watch_unindex_and_remove_only_affects_folder_sources(client, rag_instance):
    client.post("/api/index/watch/start", json={"path": "C:\\foo"})
    rag_instance.docs = [
        {"source": "C:\\foo\\a.txt", "text": "a1"},
        {"source": "C:\\foo\\a.txt", "text": "a2"},
        {"source": "C:\\foobar\\b.txt", "text": "b1"},
        {"source": "upload::manual.txt", "text": "u1"},
    ]

    unindex_resp = client.post("/api/index/watch/unindex", json={"path": "C:\\foo"})
    assert unindex_resp.status_code == 200
    assert unindex_resp.json()["removed_documents"] == 1

    remaining_sources = {row["source"] for row in rag_instance.docs}
    assert "C:\\foo\\a.txt" not in remaining_sources
    assert "C:\\foobar\\b.txt" in remaining_sources
    assert "upload::manual.txt" in remaining_sources

    remove_resp = client.post("/api/index/watch/remove", json={"path": "C:\\foo"})
    assert remove_resp.status_code == 200
    assert remove_resp.json()["status"] == "removed"
