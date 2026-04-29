"""Endpoint de subida e indexacion de documentos."""

import os
import tempfile
from typing import List

from fastapi import APIRouter, File, UploadFile

from app.core.ingest_file import process_file

router = APIRouter()


@router.post("")
async def ingest_documents(files: List[UploadFile] = File(...)):
    """Procesa archivos subidos y devuelve resumen de chunks indexados."""
    results = []
    total_chunks = 0
    for file_obj in files:
        raw_content = await file_obj.read()
        extension = os.path.splitext(file_obj.filename)[1] if file_obj.filename else ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
            tmp_file.write(raw_content)
            tmp_path = tmp_file.name

        try:
            source_name = (file_obj.filename or os.path.basename(tmp_path)).strip()
            result = process_file(tmp_path, source=f"upload::{source_name}")
            result["filename"] = file_obj.filename
            results.append(result)
            total_chunks += result.get("chunks", 0)
        finally:
            os.unlink(tmp_path)

    return {"status": "indexed", "documents": results, "indexed_chunks": total_chunks}
