from fastapi import APIRouter, UploadFile, File
from typing import List
import io
import pypdf
import docx
from app.core.ingest import chunk_text
from app.core import rag

router = APIRouter()

@router.post('')
async def ingest_documents(files: List[UploadFile] = File(...)):
    results = []
    total_chunks = 0
    for f in files:
        raw_content = await f.read()
        content = ""
        
        try:
            if f.filename.lower().endswith('.pdf'):
                reader = pypdf.PdfReader(io.BytesIO(raw_content))
                content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            elif f.filename.lower().endswith('.docx'):
                doc = docx.Document(io.BytesIO(raw_content))
                content = "\n".join([para.text for para in doc.paragraphs])
            else:
                content = raw_content.decode('utf-8', errors='ignore')
        except Exception as e:
            results.append({'filename': f.filename, 'error': str(e)})
            continue
            
        chunks = chunk_text(content)
        rag.instance.add_documents(chunks, f.filename)
        results.append({'filename': f.filename, 'chunks': len(chunks)})
        total_chunks += len(chunks)
        
    return {'status': 'indexed', 'documents': results, 'indexed_chunks': total_chunks}

