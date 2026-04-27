import os
import json
from pydantic_settings import BaseSettings

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RUNTIME_SETTINGS_PATH = os.path.join(PROJECT_ROOT, 'data', 'settings.json')


class Settings(BaseSettings):
    project_name: str = 'local-rag'
    embedding_model: str = 'all-MiniLM-L6-v2'
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    relevance_threshold: float = 0.45
    default_mode: str = 'rag'
    default_model: str = 'llama-3.1-8b'
    llm_model_path: str = os.path.join(PROJECT_ROOT, 'data', 'models', 'Qwen3.5-0.8B-BF16.gguf')
    llm_context_window: int = 4096
    llm_max_tokens: int = 512
    enable_web_fallback: bool = True
    web_search_max_results: int = 3


settings = Settings()


# ── Configuración dinámica persistida en data/settings.json ──────────────────

def _load_runtime() -> dict:
    """Carga la configuración dinámica guardada en disco."""
    if os.path.exists(RUNTIME_SETTINGS_PATH):
        try:
            with open(RUNTIME_SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_runtime(data: dict):
    """Persiste la configuración dinámica en disco."""
    os.makedirs(os.path.dirname(RUNTIME_SETTINGS_PATH), exist_ok=True)
    with open(RUNTIME_SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_watch_folders() -> list[str]:
    """Devuelve la lista de carpetas vigiladas guardadas."""
    return _load_runtime().get('watch_folders', [])


def save_watch_folders(paths: list[str]):
    """Persiste la lista de carpetas vigiladas."""
    data = _load_runtime()
    data['watch_folders'] = paths
    _save_runtime(data)
