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
    history: list = []

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
    
    if not results or (scores and scores[0] < settings.relevance_threshold):
        if settings.enable_web_fallback:
            from app.core.web_search import perform_web_search
            web_context, web_sources = perform_web_search(request.query)
            
            answer = rag.instance.generate_answer(request.query, web_context, is_web_fallback=True, history=request.history)
            final_sources = web_sources if web_sources else ['⚠️ Búsqueda web fallida (sin resultados)']
            return {
                'answer': answer,
                'sources': final_sources,
                'used_web': True,
                'scores': scores
            }
                
        answer = rag.instance.generate_answer(request.query, "", is_fallback=True, history=request.history)
        return {
            'answer': answer,
            'sources': ['📡 Base de Conocimiento Interna (LLM)'],
            'used_web': False,
            'scores': scores
        }
    context = "\n".join([r['text'] for r in results])
    sources_list = [f"{r['source']}" for r in results]
    
    # Generar la respuesta real con el motor Qwen
    answer = rag.instance.generate_answer(request.query, context, history=request.history)
    
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

    if not results or (scores and scores[0] < settings.relevance_threshold):
        async def fallback_generator():
            try:
                if settings.enable_web_fallback:
                    from app.core.web_search import perform_web_search
                    web_context, web_sources = perform_web_search(request.query)
                    
                    for token in rag.instance.generate_answer_stream(request.query, web_context, is_web_fallback=True, history=request.history):
                        yield f"data: {json.dumps({'token': token, 'done': False, 'sources': []})}\n\n"
                    
                    final_sources = web_sources if web_sources else ['⚠️ Búsqueda web fallida (sin resultados)']
                    yield f"data: {json.dumps({'token': '', 'done': True, 'sources': final_sources})}\n\n"
                    return

                for token in rag.instance.generate_answer_stream(request.query, "", is_fallback=True, history=request.history):
                    yield f"data: {json.dumps({'token': token, 'done': False, 'sources': []})}\n\n"
                yield f"data: {json.dumps({'token': '', 'done': True, 'sources': ['📡 Base de Conocimiento Interna (LLM)']})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'token': f'[Error]: {str(e)}', 'done': True, 'sources': []})}\n\n"
        return StreamingResponse(fallback_generator(), media_type="text/event-stream")

    context = "\n".join([r['text'] for r in results])

    async def token_generator():
        try:
            for token in rag.instance.generate_answer_stream(request.query, context, history=request.history):
                yield f"data: {json.dumps({'token': token, 'done': False, 'sources': []})}\n\n"
            # Señal final con las fuentes
            yield f"data: {json.dumps({'token': '', 'done': True, 'sources': sources_list})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'token': f'[Error]: {str(e)}', 'done': True, 'sources': []})}\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")
