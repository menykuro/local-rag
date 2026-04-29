"""Endpoints de consulta RAG con respuesta completa y por streaming SSE."""

import json
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core import rag
from app.core.config import settings

router = APIRouter()


class QueryRequest(BaseModel):
    """Payload de consulta enviado desde frontend."""

    query: str
    top_k: int = settings.top_k
    mode: str = settings.default_mode
    model: str = settings.default_model
    history: list = []


class QueryResult(BaseModel):
    """Respuesta normalizada devuelta por el endpoint no-streaming."""

    answer: str
    sources: list
    used_web: bool = False
    scores: list = []


def _filter_relevant_results(results: list, scores: list) -> tuple[list, list]:
    """Filtra chunks por umbral de relevancia para reducir ruido."""
    filtered = [(result, score) for result, score in zip(results, scores) if score >= settings.relevance_threshold]
    return [result for result, _ in filtered], [score for _, score in filtered]


@router.post("", response_model=QueryResult)
async def search(request: QueryRequest):
    """Resuelve una consulta RAG y cae a web o LLM local si no hay contexto relevante."""
    if request.mode == "web":
        return {
            "answer": f"[{request.model}] (Web mode mock) Response for: {request.query}",
            "sources": ["web-search-mock"],
            "used_web": True,
            "scores": [],
        }

    results, scores = rag.instance.search(request.query, request.top_k)
    results, scores = _filter_relevant_results(results, scores)

    if not results:
        if settings.enable_web_fallback:
            from app.core.web_search import perform_web_search

            web_context, web_sources = perform_web_search(request.query)
            answer = rag.instance.generate_answer(
                request.query, web_context, is_web_fallback=True, history=request.history
            )
            final_sources = web_sources if web_sources else ["Busqueda web fallida (sin resultados)"]
            return {"answer": answer, "sources": final_sources, "used_web": True, "scores": scores}

        answer = rag.instance.generate_answer(request.query, "", is_fallback=True, history=request.history)
        return {
            "answer": answer,
            "sources": ["Base de Conocimiento Interna (LLM)"],
            "used_web": False,
            "scores": scores,
        }

    context = "\n".join([row["text"] for row in results])
    sources_list = [f"{row['source']}" for row in results]
    answer = rag.instance.generate_answer(request.query, context, history=request.history)
    return {"answer": f"[{request.model}] {answer}", "sources": list(set(sources_list)), "used_web": False, "scores": scores}


@router.post("/stream")
async def search_stream(request: QueryRequest):
    """Devuelve tokens SSE y envia fuentes al finalizar."""
    results, scores = rag.instance.search(request.query, request.top_k)
    results, scores = _filter_relevant_results(results, scores)
    sources_list = list(set(row["source"] for row in results)) if results else []

    if not results:

        async def fallback_generator():
            try:
                if settings.enable_web_fallback:
                    from app.core.web_search import perform_web_search

                    web_context, web_sources = perform_web_search(request.query)
                    for token in rag.instance.generate_answer_stream(
                        request.query, web_context, is_web_fallback=True, history=request.history
                    ):
                        yield f"data: {json.dumps({'token': token, 'done': False, 'sources': []})}\n\n"
                    final_sources = web_sources if web_sources else ["Busqueda web fallida (sin resultados)"]
                    yield f"data: {json.dumps({'token': '', 'done': True, 'sources': final_sources})}\n\n"
                    return

                for token in rag.instance.generate_answer_stream(request.query, "", is_fallback=True, history=request.history):
                    yield f"data: {json.dumps({'token': token, 'done': False, 'sources': []})}\n\n"
                yield f"data: {json.dumps({'token': '', 'done': True, 'sources': ['Base de Conocimiento Interna (LLM)']})}\n\n"
            except Exception as exc:
                yield f"data: {json.dumps({'token': f'[Error]: {str(exc)}', 'done': True, 'sources': []})}\n\n"

        return StreamingResponse(fallback_generator(), media_type="text/event-stream")

    context = "\n".join([row["text"] for row in results])

    async def token_generator():
        try:
            for token in rag.instance.generate_answer_stream(request.query, context, history=request.history):
                yield f"data: {json.dumps({'token': token, 'done': False, 'sources': []})}\n\n"
            yield f"data: {json.dumps({'token': '', 'done': True, 'sources': sources_list})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'token': f'[Error]: {str(exc)}', 'done': True, 'sources': []})}\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")
