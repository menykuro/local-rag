from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core import rag
from app.core import watch_folder as watcher_module
from app.core.config import get_watch_folders, save_watch_folders

router = APIRouter()


# ── Gestión del índice FAISS ──────────────────────────────────────────────────

@router.post('/clear')
async def clear_index():
    rag.instance.clear()
    return {"status": "cleared"}

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
    return {"status": "deleted", "source": source}


# ── Watch Folder ──────────────────────────────────────────────────────────────

class WatchRequest(BaseModel):
    path: str
    recursive: bool = False


@router.post('/watch/start')
async def start_watch(request: WatchRequest):
    """Activa la vigilancia de una carpeta y la persiste en settings.json."""
    import os
    path = os.path.normpath(request.path)

    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"La ruta '{path}' no existe o no es una carpeta.")

    if watcher_module.instance.is_watching(path):
        return {"status": "already_watching", "path": path}

    started = watcher_module.instance.start(path, recursive=request.recursive)
    if not started:
        raise HTTPException(status_code=500, detail="No se pudo iniciar el watcher.")

    # Persistir la lista actualizada
    current = get_watch_folders()
    if path not in current:
        current.append(path)
        save_watch_folders(current)

    return {"status": "started", "path": path}


@router.post('/watch/stop')
async def stop_watch(request: WatchRequest):
    """Detiene la vigilancia de una carpeta concreta."""
    import os
    path = os.path.normpath(request.path)

    stopped = watcher_module.instance.stop(path)
    if not stopped:
        raise HTTPException(status_code=404, detail=f"No hay watcher activo para '{path}'.")

    # Eliminar de la persistencia
    current = get_watch_folders()
    if path in current:
        current.remove(path)
        save_watch_folders(current)

    return {"status": "stopped", "path": path}


@router.get('/watch/status')
async def watch_status():
    """Devuelve el estado actual de todos los watchers activos."""
    return watcher_module.instance.status()

@router.get('/watch/select-folder')
async def select_folder():
    """Abre un diálogo nativo para seleccionar una carpeta."""
    import tkinter as tk
    from tkinter import filedialog
    import threading
    
    path_container = []
    def ask_folder():
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askdirectory()
        if path:
            path_container.append(path)
        root.destroy()

    # Ejecutar en un hilo separado para no bloquear FastAPI si hay problemas
    t = threading.Thread(target=ask_folder)
    t.start()
    t.join()
    
    if path_container:
        return {"path": path_container[0]}
    return {"path": ""}

@router.post('/watch/untrack')
async def untrack_watch(request: WatchRequest):
    """Deja de vigilar una carpeta (detiene el watcher) pero la mantiene en la lista."""
    import os
    path = os.path.normpath(request.path)
    stopped = watcher_module.instance.stop(path)
    return {"status": "untracked", "path": path, "was_running": stopped}

@router.post('/watch/unindex')
async def unindex_watch(request: WatchRequest):
    """Detiene la vigilancia y elimina todos los chunks asociados a esa carpeta."""
    import os
    path = os.path.normpath(request.path)
    
    # 1. Detener watcher
    watcher_module.instance.stop(path)
    
    # 2. Identificar documentos que pertenecen a esa carpeta
    # Como ahora usamos rutas absolutas, buscamos los que empiecen por esa ruta
    sources_to_remove = [
        doc["source"] for doc in rag.instance.list_documents()
        if os.path.normpath(doc["source"]).startswith(path)
    ]
    
    removed_count = 0
    if sources_to_remove:
        removed_count = rag.instance.delete_documents_by_sources(sources_to_remove)
    
    return {"status": "unindexed", "path": path, "removed_documents": removed_count}

@router.post('/watch/remove')
async def remove_watch(request: WatchRequest):
    """Detiene, desindexa y elimina de la configuración."""
    import os
    path = os.path.normpath(request.path)
    
    # 1. Desindexar (esto ya detiene el watcher)
    await unindex_watch(request)
    
    # 2. Eliminar de la persistencia
    current = get_watch_folders()
    if path in current:
        current.remove(path)
        save_watch_folders(current)
        
    return {"status": "removed", "path": path}
