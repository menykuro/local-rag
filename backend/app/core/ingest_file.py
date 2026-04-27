"""Módulo compartido para procesar archivos desde disco (usado por API y Watch Folder)."""
import logging
import io
import re
import os
import pdfplumber
import docx
from app.core.ingest import chunk_text
from app.core import rag
from app.core.config import normalize_watch_path

SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md', '.markdown'}


def is_supported_file(file_path: str) -> bool:
    """Verifica si un archivo tiene extensión compatible."""
    _, ext = os.path.splitext(file_path)
    return ext.lower() in SUPPORTED_EXTENSIONS


def extract_text(file_path: str) -> str:
    """Extrae texto de un archivo según su extensión."""
    ext = os.path.splitext(file_path)[1].lower()

    with open(file_path, 'rb') as f:
        raw_content = f.read()

    if ext == '.pdf':
        with pdfplumber.open(io.BytesIO(raw_content)) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text(layout=True) or ""
                lines = [line.rstrip() for line in text.split('\n')]
                text_clean = '\n'.join(lines)
                text = re.sub(r' {3,}', ' | ', text_clean)
                if text.strip():
                    pages_text.append(text)
            return "\n".join(pages_text)

    elif ext == '.docx':
        doc = docx.Document(io.BytesIO(raw_content))
        return "\n".join([para.text for para in doc.paragraphs])

    else:
        return raw_content.decode('utf-8', errors='ignore')


def process_file(file_path: str, source: str | None = None) -> dict:
    """Procesa un archivo: extrae texto, genera chunks e indexa en FAISS.
    
    Returns:
        dict con 'filename' y 'chunks' o 'error'.
    """
    abs_path = os.path.abspath(file_path)
    if source and source.startswith("upload::"):
        source_id = source
    elif source:
        source_id = normalize_watch_path(source)
    else:
        source_id = normalize_watch_path(abs_path)
    filename = os.path.basename(abs_path)
    try:
        content = extract_text(abs_path)
        if not content.strip():
            return {'filename': filename, 'chunks': 0}

        chunks = chunk_text(content)
        rag.instance.add_documents(chunks, source_id)
        logging.info(f"[Watch] Indexado: {filename} ({len(chunks)} chunks)")
        return {'filename': filename, 'chunks': len(chunks)}
    except Exception as e:
        logging.error(f"[Watch] Error procesando {filename}: {str(e)}")
        return {'filename': filename, 'error': str(e)}
