"""Endpoints de salud del servicio."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/rag")
async def rag(query: str):
    """Endpoint de prueba historico para validar el enrutado."""
    return {"answer": "RAG response placeholder", "query": query}
