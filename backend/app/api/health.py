from fastapi import APIRouter

router = APIRouter()

@router.post('/rag')
async def rag(query: str):
    return {'answer': 'RAG response placeholder', 'query': query}
