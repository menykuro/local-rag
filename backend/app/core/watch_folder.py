"""Servicio de vigilancia de carpetas para ingesta automática de documentos."""
import logging
import os
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.core.ingest_file import is_supported_file, process_file
from app.core.config import normalize_watch_path


class _FileEventHandler(FileSystemEventHandler):
    """Manejador de eventos del sistema de ficheros para una carpeta vigilada."""

    def __init__(self, path: str, debounce_seconds: float = 1.25):
        super().__init__()
        self.path = normalize_watch_path(path)
        self._debounce_seconds = debounce_seconds
        self._processing_lock = threading.Lock()
        self._last_processed_at: dict[str, float] = {}

    def _handle(self, file_path: str):
        """Procesa un archivo si es compatible y no está en ventana de debounce."""
        normalized_file = normalize_watch_path(file_path)
        if not is_supported_file(normalized_file):
            return

        now = time.monotonic()
        with self._processing_lock:
            previous = self._last_processed_at.get(normalized_file)
            if previous is not None and (now - previous) < self._debounce_seconds:
                return
            self._last_processed_at[normalized_file] = now

        logging.info(f"[Watch] Detectado cambio en archivo: {normalized_file}")
        process_file(normalized_file)

    def on_created(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle(event.src_path)


class WatcherService:
    """Singleton que gestiona múltiples Observers de watchdog."""

    def __init__(self):
        self._observers: dict[str, Observer] = {}
        self._lock = threading.Lock()

    def _scan_existing(self, path: str):
        """Indexa archivos compatibles ya existentes en la carpeta."""
        logging.info(f"[Watch] Escaneando archivos existentes en: {path}")
        for root, _, files in os.walk(path):
            for filename in files:
                file_path = os.path.join(root, filename)
                if is_supported_file(file_path):
                    process_file(file_path)

    def start(self, path: str, recursive: bool = True) -> bool:
        """Inicia la vigilancia de una carpeta. Devuelve True si se activó."""
        normalized_path = normalize_watch_path(path)
        with self._lock:
            if normalized_path in self._observers:
                logging.info(f"[Watch] Ya está siendo vigilada: {normalized_path}")
                return False
            if not os.path.isdir(normalized_path):
                logging.error(f"[Watch] La ruta no existe o no es una carpeta: {normalized_path}")
                return False

            threading.Thread(
                target=self._scan_existing,
                args=(normalized_path,),
                daemon=True,
                name=f"watch-scan-{os.path.basename(normalized_path)}",
            ).start()

            handler = _FileEventHandler(normalized_path)
            observer = Observer()
            observer.schedule(handler, normalized_path, recursive=recursive)
            observer.start()
            self._observers[normalized_path] = observer
            logging.info(f"[Watch] Vigilancia activa en: {normalized_path}")
            return True

    def stop(self, path: str) -> bool:
        """Detiene la vigilancia de una carpeta concreta. Devuelve True si estaba activa."""
        normalized_path = normalize_watch_path(path)
        with self._lock:
            observer = self._observers.pop(normalized_path, None)
            if observer is None:
                return False
            observer.stop()
            observer.join()
            logging.info(f"[Watch] Vigilancia detenida: {normalized_path}")
            return True

    def stop_all(self):
        """Detiene todos los observers activos. Llamar al apagar el servidor."""
        with self._lock:
            for path, observer in list(self._observers.items()):
                observer.stop()
                observer.join()
                logging.info(f"[Watch] Observer detenido: {path}")
            self._observers.clear()

    def active_paths(self) -> list[str]:
        with self._lock:
            return list(self._observers.keys())

    def is_watching(self, path: str) -> bool:
        return normalize_watch_path(path) in self._observers


instance = WatcherService()
