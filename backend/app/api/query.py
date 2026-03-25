from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core import rag
from app.core.config import settings

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    top_k: int = settings.top_k
    mode: str = settings.default_mode
    model: str = settings.default_model

class QueryResult(BaseModel):
    answer: str
    sources: list
    used_web: bool = False
    scores: list = []

@router.post('', response_model=QueryResult)
async def search(request: QueryRequest):
    if request.mode == "web":
        return {
            'answer': f'[{request.model}] (Web mode mock) Response for: {request.query}', 
            'sources': ['web-search-mock'], 
            'used_web': True,
            'scores': []
        }
        
    # RAG mode
    results, scores = rag.instance.search(request.query, request.top_k)
    
    if not results:
        return {
            'answer': f'[{request.model}] No local context found. Fallback or generic response for: {request.query}',
            'sources': [],
            'used_web': False,
            'scores': []
        }
    
    # Check threshold using the first (best) score
    if scores and scores[0] < settings.relevance_threshold:
        # Based on AC3/AC4 logic, if score < threshold, maybe warn or fallback
        pass
        
    context = "\n".join([r['text'] for r in results])
    sources_list = [f"{r['source']}" for r in results]
    
    answer = f'[{request.model}] Based on local context:\n{context[:100]}...\nGenerative answer for: {request.query}'
    
    return {
        'answer': answer, 
        'sources': sources_list, 
        'used_web': False,
        'scores': scores
    }

