"""Fixtures de pruebas para backend API y componentes core."""

import copy
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


class DummyRagInstance:
    def __init__(self):
        self.reset()

    def reset(self):
        self.docs = []
        self.search_results = ([], [])
        self.answer_text = "dummy-answer"
        self.stream_tokens = ["dummy"]
        self.stats = {"doc_count": 0, "chunk_count": 0, "index_size": "0KB"}
        self.last_generate = None

    def clear(self):
        self.docs = []

    def list_documents(self):
        by_source = {}
        for row in self.docs:
            src = row["source"]
            if src not in by_source:
                by_source[src] = {"source": src, "display_name": src.split("upload::")[-1], "chunks": 0}
            by_source[src]["chunks"] += 1
        return list(by_source.values())

    def delete_document(self, source):
        original = len(self.docs)
        self.docs = [row for row in self.docs if row["source"] != source]
        return len(self.docs) != original

    def delete_documents_by_sources(self, sources):
        sources_set = set(sources)
        removed_sources = {row["source"] for row in self.docs if row["source"] in sources_set}
        self.docs = [row for row in self.docs if row["source"] not in sources_set]
        return len(removed_sources)

    def add_documents(self, chunks, source, replace_source=True):
        if replace_source:
            self.docs = [row for row in self.docs if row["source"] != source]
        for chunk in chunks:
            self.docs.append({"source": source, "text": chunk})

    def search(self, query, top_k=5):
        return copy.deepcopy(self.search_results)

    def generate_answer(self, query, context, is_fallback=False, is_web_fallback=False, history=None):
        self.last_generate = {
            "query": query,
            "context": context,
            "is_fallback": is_fallback,
            "is_web_fallback": is_web_fallback,
            "history": history or [],
        }
        return self.answer_text

    def generate_answer_stream(self, query, context, is_fallback=False, is_web_fallback=False, history=None):
        self.last_generate = {
            "query": query,
            "context": context,
            "is_fallback": is_fallback,
            "is_web_fallback": is_web_fallback,
            "history": history or [],
        }
        for token in self.stream_tokens:
            yield token

    def get_stats(self):
        return copy.deepcopy(self.stats)


class FakeWatcher:
    def __init__(self):
        self.active = {}
        self.started = []
        self.stopped = []

    def start(self, path, recursive=True):
        if path in self.active:
            return False
        self.active[path] = recursive
        self.started.append((path, recursive))
        return True

    def stop(self, path):
        existed = path in self.active
        if existed:
            del self.active[path]
            self.stopped.append(path)
        return existed

    def stop_all(self):
        self.active = {}

    def active_paths(self):
        return list(self.active.keys())

    def is_watching(self, path):
        return path in self.active


dummy_rag_module = types.ModuleType("app.core.rag")
dummy_rag_module.instance = DummyRagInstance()
sys.modules["app.core.rag"] = dummy_rag_module


@pytest.fixture()
def rag_instance():
    inst = sys.modules["app.core.rag"].instance
    inst.reset()
    return inst


@pytest.fixture()
def temp_runtime_settings(tmp_path, monkeypatch):
    import app.core.config as config

    runtime_file = tmp_path / "settings.json"
    monkeypatch.setattr(config, "RUNTIME_SETTINGS_PATH", str(runtime_file))
    return runtime_file


@pytest.fixture()
def client(monkeypatch, temp_runtime_settings, rag_instance):
    from app import main
    from app.api import index as index_api

    fake_watcher = FakeWatcher()
    monkeypatch.setattr(index_api.watcher_module, "instance", fake_watcher, raising=True)
    monkeypatch.setattr(main.watcher_module, "instance", fake_watcher, raising=True)
    monkeypatch.setattr(main, "get_watch_folders", lambda: [])
    monkeypatch.setattr(index_api.os.path, "isdir", lambda p: True)

    with TestClient(main.app) as test_client:
        yield test_client

