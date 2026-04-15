from fastapi import APIRouter
from fastapi.responses import StreamingResponse
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
    
    # Generar la respuesta real con el motor Qwen
    answer = rag.instance.generate_answer(request.query, context)
    
    return {
        'answer': f'[{request.model}] {answer}', 
        'sources': list(set(sources_list)), 
        'used_web': False,
        'scores': scores
    }


@router.post('/stream')
async def search_stream(request: QueryRequest):
    """Endpoint de streaming SSE: devuelve tokens de Qwen en tiempo real."""
    import json

    results, scores = rag.instance.search(request.query, request.top_k)
    sources_list = list(set(r['source'] for r in results)) if results else []

    if not results:
        async def no_context():
            yield f"data: {json.dumps({'token': 'No se encontró contexto relevante para tu pregunta.', 'done': True, 'sources': []})}\n\n"
        return StreamingResponse(no_context(), media_type="text/event-stream")

    context = "\n".join([r['text'] for r in results])

    async def token_generator():
        try:
            for token in rag.instance.generate_answer_stream(request.query, context):
                yield f"data: {json.dumps({'token': token, 'done': False, 'sources': []})}\n\n"
            # Señal final con las fuentes
            yield f"data: {json.dumps({'token': '', 'done': True, 'sources': sources_list})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'token': f'[Error]: {str(e)}', 'done': True, 'sources': []})}\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")
