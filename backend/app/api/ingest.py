from fastapi import APIRouter, UploadFile, File
from typing import List
from app.core.ingest import chunk_text
from app.core import rag

router = APIRouter()

@router.post('')
async def ingest_documents(files: List[UploadFile] = File(...)):
    results = []
    total_chunks = 0
    for f in files:
        content = (await f.read()).decode('utf-8', errors='ignore')
        chunks = chunk_text(content)
        rag.instance.add_documents(chunks, f.filename)
        results.append({'filename': f.filename, 'chunks': len(chunks)})
        total_chunks += len(chunks)
        
    return {'status': 'indexed', 'documents': results, 'indexed_chunks': total_chunks}

