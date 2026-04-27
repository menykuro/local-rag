import os
import threading
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core import rag
from app.core import watch_folder as watcher_module
from app.core.config import (
    get_watch_folders,
    normalize_watch_path,
    remove_watch_folder,
    set_watch_folder_active,
    upsert_watch_folder,
)

router = APIRouter()


@router.post('/clear')
async def clear_index():
    rag.instance.clear()
    return {'status': 'cleared'}


@router.get('/documents')
async def list_documents():
    """Lista todos los documentos indexados con su número de chunks."""
    return rag.instance.list_documents()


@router.delete('/documents/{source:path}')
async def delete_document(source: str):
    """Elimina un documento concreto del índice por nombre de fuente."""
    deleted = rag.instance.delete_document(source)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Documento '{source}' no encontrado en el índice.")
    return {'status': 'deleted', 'source': source}


class WatchRequest(BaseModel):
    path: str
    recursive: bool = True


def _build_watch_status() -> dict:
    configured = get_watch_folders()
    active_paths = set(os.path.normcase(p) for p in watcher_module.instance.active_paths())

    folders = []
    for item in configured:
        path = normalize_watch_path(item['path'])
        is_active = os.path.normcase(path) in active_paths
        folders.append(
            {
                'path': path,
                'active': is_active,
                'recursive': bool(item.get('recursive', True)),
            }
        )

    return {
        'running': any(item['active'] for item in folders),
        'active_count': sum(1 for item in folders if item['active']),
        'total_count': len(folders),
        'folders': folders,
        'paths': [item['path'] for item in folders],
    }


def _is_source_inside_folder(source: str, folder_path: str) -> bool:
    if source.startswith('upload::'):
        return False

    source_path = normalize_watch_path(source)
    folder_norm = normalize_watch_path(folder_path)

    try:
        common = os.path.commonpath([source_path, folder_norm])
    except ValueError:
        return False

    return os.path.normcase(common) == os.path.normcase(folder_norm)


@router.post('/watch/start')
async def start_watch(request: WatchRequest):
    """Añade una ruta al watch y la deja activa (idempotente)."""
    path = normalize_watch_path(request.path)
    recursive = bool(request.recursive)

    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"La ruta '{path}' no existe o no es una carpeta.")

    upsert_watch_folder(path=path, active=True, recursive=recursive)
    if not watcher_module.instance.is_watching(path):
        started = watcher_module.instance.start(path, recursive=recursive)
        if not started:
            raise HTTPException(status_code=500, detail='No se pudo iniciar el watcher.')

    return {'status': 'started', 'path': path, 'recursive': recursive}


@router.post('/watch/pause')
async def pause_watch(request: WatchRequest):
    """Pausa vigilancia de una ruta, manteniéndola en settings.json."""
    path = normalize_watch_path(request.path)
    exists = set_watch_folder_active(path, False)
    if not exists:
        raise HTTPException(status_code=404, detail=f"Ruta no configurada: '{path}'.")

    was_running = watcher_module.instance.stop(path)
    return {'status': 'paused', 'path': path, 'was_running': was_running}


@router.post('/watch/resume')
async def resume_watch(request: WatchRequest):
    """Reanuda vigilancia de una ruta ya configurada."""
    path = normalize_watch_path(request.path)
    recursive = bool(request.recursive)

    folders = get_watch_folders()
    target = None
    for item in folders:
        if os.path.normcase(normalize_watch_path(item['path'])) == os.path.normcase(path):
            target = item
            break

    if target is None:
        raise HTTPException(status_code=404, detail=f"Ruta no configurada: '{path}'.")
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"La ruta '{path}' no existe o no es una carpeta.")

    recursive = bool(target.get('recursive', recursive))
    upsert_watch_folder(path=path, active=True, recursive=recursive)

    if not watcher_module.instance.is_watching(path):
        started = watcher_module.instance.start(path, recursive=recursive)
        if not started:
            raise HTTPException(status_code=500, detail='No se pudo reanudar el watcher.')

    return {'status': 'resumed', 'path': path, 'recursive': recursive}


@router.post('/watch/pause-all')
async def pause_all_watchers():
    folders = get_watch_folders()
    for item in folders:
        set_watch_folder_active(item['path'], False)
        watcher_module.instance.stop(item['path'])
    return {'status': 'paused_all', 'count': len(folders)}


@router.post('/watch/resume-all')
async def resume_all_watchers():
    folders = get_watch_folders()
    resumed = 0
    skipped = []

    for item in folders:
        path = item['path']
        recursive = bool(item.get('recursive', True))
        if not os.path.isdir(path):
            skipped.append(path)
            continue

        upsert_watch_folder(path=path, active=True, recursive=recursive)
        if not watcher_module.instance.is_watching(path):
            watcher_module.instance.start(path, recursive=recursive)
        resumed += 1

    return {'status': 'resumed_all', 'resumed': resumed, 'skipped': skipped}


@router.get('/watch/status')
async def watch_status():
    """Devuelve estado de rutas configuradas y cuáles están activas."""
    return _build_watch_status()


@router.get('/watch/select-folder')
async def select_folder():
    """Abre un diálogo nativo para seleccionar carpeta (fallback: cadena vacía)."""
    path_container: list[str] = []

    def ask_folder():
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes('-topmost', True)
            except Exception:
                pass
            path = filedialog.askdirectory()
            if path:
                path_container.append(path)
            root.destroy()
        except Exception:
            # fallback silencioso para que el usuario use input manual
            return

    thread = threading.Thread(target=ask_folder, daemon=True)
    thread.start()
    thread.join(timeout=120)

    if path_container:
        return {'path': normalize_watch_path(path_container[0])}
    return {'path': ''}


@router.post('/watch/unindex')
async def unindex_watch(request: WatchRequest):
    """Pausa una carpeta y elimina sus chunks del índice."""
    path = normalize_watch_path(request.path)

    if not set_watch_folder_active(path, False):
        raise HTTPException(status_code=404, detail=f"Ruta no configurada: '{path}'.")

    watcher_module.instance.stop(path)

    sources_to_remove = [
        doc['source']
        for doc in rag.instance.list_documents()
        if _is_source_inside_folder(doc['source'], path)
    ]

    removed_count = 0
    if sources_to_remove:
        removed_count = rag.instance.delete_documents_by_sources(sources_to_remove)

    return {'status': 'unindexed', 'path': path, 'removed_documents': removed_count}


@router.post('/watch/remove')
async def remove_watch(request: WatchRequest):
    """Pausa, desindexa y elimina ruta de configuración."""
    path = normalize_watch_path(request.path)

    if not any(os.path.normcase(item['path']) == os.path.normcase(path) for item in get_watch_folders()):
        raise HTTPException(status_code=404, detail=f"Ruta no configurada: '{path}'.")

    await unindex_watch(request)
    remove_watch_folder(path)

    return {'status': 'removed', 'path': path}


# Alias de compatibilidad hacia atrás
@router.post('/watch/untrack')
async def untrack_watch(request: WatchRequest):
    return await pause_watch(request)


@router.post('/watch/stop')
async def stop_watch(request: WatchRequest):
    return await pause_watch(request)
