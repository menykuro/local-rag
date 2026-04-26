from fastapi import APIRouter, HTTPException
from app.core import rag

router = APIRouter()

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
