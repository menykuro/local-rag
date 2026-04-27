"""Servicio de vigilancia de carpetas para ingesta automática de documentos."""
import logging
import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.core.ingest_file import is_supported_file, process_file


class _FileEventHandler(FileSystemEventHandler):
    """Manejador de eventos del sistema de ficheros para una carpeta vigilada."""

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        # Evitar re-indexar el mismo archivo si llegan dos eventos seguidos
        self._processing_lock = threading.Lock()

    def _handle(self, file_path: str):
        """Procesa un archivo si es compatible y no está siendo ya procesado."""
        if not is_supported_file(file_path):
            return
        # Pequeño lock para evitar dobles eventos (created + modified) simultáneos
        with self._processing_lock:
            logging.info(f"[Watch] Detectado nuevo archivo: {file_path}")
            process_file(file_path)

    def on_created(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle(event.src_path)


class WatcherService:
    """Singleton que gestiona múltiples Observers de watchdog."""

    def __init__(self):
        self._observers: dict[str, Observer] = {}  # path -> Observer
        self._lock = threading.Lock()

    def _scan_existing(self, path: str):
        """Indexa todos los archivos compatibles ya existentes en la carpeta."""
        logging.info(f"[Watch] Escaneando archivos existentes en: {path}")
        for root, _, files in os.walk(path):
            for filename in files:
                file_path = os.path.join(root, filename)
                if is_supported_file(file_path):
                    process_file(file_path)

    def start(self, path: str, recursive: bool = False) -> bool:
        """Inicia la vigilancia de una carpeta. Devuelve True si se activó."""
        path = os.path.normpath(path)
        with self._lock:
            if path in self._observers:
                logging.info(f"[Watch] Ya está siendo vigilada: {path}")
                return False
            if not os.path.isdir(path):
                logging.error(f"[Watch] La ruta no existe o no es una carpeta: {path}")
                return False

            # Escanear los archivos existentes primero en un hilo aparte
            threading.Thread(
                target=self._scan_existing,
                args=(path,),
                daemon=True,
                name=f"watch-scan-{os.path.basename(path)}"
            ).start()

            handler = _FileEventHandler(path)
            observer = Observer()
            observer.schedule(handler, path, recursive=recursive)
            observer.start()
            self._observers[path] = observer
            logging.info(f"[Watch] Vigilancia activa en: {path}")
            return True

    def stop(self, path: str) -> bool:
        """Detiene la vigilancia de una carpeta concreta. Devuelve True si estaba activa."""
        path = os.path.normpath(path)
        with self._lock:
            observer = self._observers.pop(path, None)
            if observer is None:
                return False
            observer.stop()
            observer.join()
            logging.info(f"[Watch] Vigilancia detenida: {path}")
            return True

    def stop_all(self):
        """Detiene todos los observers activos. Llamar al apagar el servidor."""
        with self._lock:
            for path, observer in list(self._observers.items()):
                observer.stop()
                observer.join()
                logging.info(f"[Watch] Observer detenido: {path}")
            self._observers.clear()

    def status(self) -> dict:
        """Devuelve el estado actual de todos los watchers."""
        with self._lock:
            return {
                "running": len(self._observers) > 0,
                "paths": list(self._observers.keys()),
            }

    def is_watching(self, path: str) -> bool:
        return os.path.normpath(path) in self._observers


# Singleton global
instance = WatcherService()
