import logging
from fastapi import APIRouter, UploadFile, File
from typing import List
import io
import re
import pdfplumber
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
                # Usar pdfplumber para extraer texto preservando el layout (tablas)
                with pdfplumber.open(io.BytesIO(raw_content)) as pdf:
                    pages_text = []
                    for page in pdf.pages:
                        # Usamos layout=True para mantener la posición visual (columnas/tablas)
                        text = page.extract_text(layout=True) or ""
                        
                        # Limpiar las líneas y transformar grandes espacios en separadores de tabla " | "
                        lines = [line.rstrip() for line in text.split('\n')]
                        text_clean = '\n'.join(lines)
                        text = re.sub(r' {3,}', ' | ', text_clean)
                                
                        if text.strip():
                            pages_text.append(text)
                    content = "\n".join(pages_text)
            elif f.filename.lower().endswith('.docx'):
                doc = docx.Document(io.BytesIO(raw_content))
                content = "\n".join([para.text for para in doc.paragraphs])
            else:
                content = raw_content.decode('utf-8', errors='ignore')
        except Exception as e:
            logging.error(f"Error procesando el archivo {f.filename}: {str(e)}")
            results.append({'filename': f.filename, 'error': str(e)})
            continue
            
        chunks = chunk_text(content)
        rag.instance.add_documents(chunks, f.filename)
        results.append({'filename': f.filename, 'chunks': len(chunks)})
        total_chunks += len(chunks)
        
    return {'status': 'indexed', 'documents': results, 'indexed_chunks': total_chunks}
