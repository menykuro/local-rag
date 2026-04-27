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


def normalize_watch_path(path: str) -> str:
    """Normaliza una ruta para guardado y comparación."""
    return os.path.normpath(os.path.abspath(path.strip()))


def _watch_key(path: str) -> str:
    return os.path.normcase(normalize_watch_path(path))


def _normalize_watch_entry(entry: dict) -> dict | None:
    path = entry.get('path', '')
    if not isinstance(path, str) or not path.strip():
        return None
    return {
        'path': normalize_watch_path(path),
        'active': bool(entry.get('active', True)),
        'recursive': bool(entry.get('recursive', True)),
    }


def _normalize_watch_entries(raw: list) -> tuple[list[dict], bool]:
    """Normaliza entradas y detecta si hubo migración/cambios."""
    changed = False
    result: list[dict] = []
    seen: set[str] = set()

    for item in raw:
        entry = None
        if isinstance(item, str):
            # Formato legado: ["C:\\ruta"]
            changed = True
            entry = {'path': item, 'active': True, 'recursive': True}
        elif isinstance(item, dict):
            entry = item

        if entry is None:
            changed = True
            continue

        normalized = _normalize_watch_entry(entry)
        if normalized is None:
            changed = True
            continue

        key = _watch_key(normalized['path'])
        if key in seen:
            changed = True
            continue

        seen.add(key)
        result.append(normalized)

    return result, changed


def get_watch_folders() -> list[dict]:
    """Devuelve la lista normalizada de watch folders persistidas."""
    data = _load_runtime()
    raw = data.get('watch_folders', [])
    if not isinstance(raw, list):
        raw = []
    normalized, changed = _normalize_watch_entries(raw)
    if changed:
        data['watch_folders'] = normalized
        _save_runtime(data)
    return normalized


def save_watch_folders(entries: list[dict]):
    """Persiste la lista de watch folders (normalizada y sin duplicados)."""
    normalized, _ = _normalize_watch_entries(entries or [])
    data = _load_runtime()
    data['watch_folders'] = normalized
    _save_runtime(data)


def upsert_watch_folder(path: str, active: bool = True, recursive: bool = True) -> dict:
    """Crea o actualiza una watch folder por ruta."""
    normalized_path = normalize_watch_path(path)
    key = _watch_key(normalized_path)
    entries = get_watch_folders()
    found = False

    for entry in entries:
        if _watch_key(entry['path']) == key:
            entry['path'] = normalized_path
            entry['active'] = active
            entry['recursive'] = recursive
            found = True
            break

    if not found:
        entries.append({
            'path': normalized_path,
            'active': active,
            'recursive': recursive,
        })

    save_watch_folders(entries)
    return {
        'path': normalized_path,
        'active': active,
        'recursive': recursive,
    }


def set_watch_folder_active(path: str, active: bool) -> bool:
    """Actualiza el estado activo/inactivo de una ruta si existe."""
    normalized_path = normalize_watch_path(path)
    key = _watch_key(normalized_path)
    entries = get_watch_folders()
    updated = False

    for entry in entries:
        if _watch_key(entry['path']) == key:
            entry['active'] = active
            updated = True
            break

    if updated:
        save_watch_folders(entries)
    return updated


def remove_watch_folder(path: str) -> bool:
    """Elimina una watch folder por ruta."""
    normalized_path = normalize_watch_path(path)
    key = _watch_key(normalized_path)
    entries = get_watch_folders()
    filtered = [entry for entry in entries if _watch_key(entry['path']) != key]

    if len(filtered) == len(entries):
        return False

    save_watch_folders(filtered)
    return True
