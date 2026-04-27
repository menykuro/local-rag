import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import health, ingest, query, stats, index
from app.core import watch_folder as watcher_module
from app.core.config import get_watch_folders


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida: arranca los watchers al iniciar y los detiene al apagar."""
    # ── Startup ──────────────────────────────────────────────────────────────
    persisted_paths = get_watch_folders()
    if persisted_paths:
        logging.info(f"[Startup] Procesando {len(persisted_paths)} Watch Folder(s) persistidas...")
        for item in persisted_paths:
            path = item['path']
            if item.get('active', True):
                watcher_module.instance.start(path, recursive=item.get('recursive', True))
    else:
        logging.info("[Startup] No hay Watch Folders configuradas.")

    yield  # La aplicación está corriendo aquí

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logging.info("[Shutdown] Deteniendo Watch Folders...")
    watcher_module.instance.stop_all()


app = FastAPI(title='Local RAG API', version='0.1', lifespan=lifespan)

app.include_router(health.router, prefix='/api/health', tags=['health'])
app.include_router(ingest.router, prefix='/api/ingest', tags=['ingest'])
app.include_router(query.router, prefix='/api/query', tags=['query'])
app.include_router(stats.router, prefix='/api/stats', tags=['stats'])
app.include_router(index.router, prefix='/api/index', tags=['index'])


@app.get('/')
async def root():
    return {'message': 'Local RAG API is running'}
