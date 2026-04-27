"""Endpoint de ingesta documental vía upload HTTP."""
import logging
import os
import tempfile
from fastapi import APIRouter, UploadFile, File
from typing import List
from app.core.ingest_file import process_file

router = APIRouter()

@router.post('')
async def ingest_documents(files: List[UploadFile] = File(...)):
    results = []
    total_chunks = 0
    for f in files:
        raw_content = await f.read()

        # Guardar temporalmente en disco para reutilizar process_file
        ext = os.path.splitext(f.filename)[1] if f.filename else '.tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(raw_content)
            tmp_path = tmp.name

        try:
            source_name = (f.filename or os.path.basename(tmp_path)).strip()
            result = process_file(tmp_path, source=f"upload::{source_name}")
            # Reemplazar el nombre temporal por el nombre original
            result['filename'] = f.filename
            results.append(result)
            total_chunks += result.get('chunks', 0)
        finally:
            os.unlink(tmp_path)

    return {'status': 'indexed', 'documents': results, 'indexed_chunks': total_chunks}
