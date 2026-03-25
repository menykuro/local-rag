from fastapi import FastAPI
from app.api import health, ingest, query, stats, index

app = FastAPI(title='Local RAG API', version='0.1')

app.include_router(health.router, prefix='/api/health', tags=['health'])
app.include_router(ingest.router, prefix='/api/ingest', tags=['ingest'])
app.include_router(query.router, prefix='/api/query', tags=['query'])
app.include_router(stats.router, prefix='/api/stats', tags=['stats'])
app.include_router(index.router, prefix='/api/index', tags=['index'])

@app.get('/')
async def root():
    return {'message': 'Local RAG API is running'}

