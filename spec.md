# Spec Driven Development (Spec) - Local RAG

## 0. Contexto
Proyecto: RAG local + Reflex. Objetivo: respuesta a preguntas sobre documentación local con modelo descargado.

> **Nota sobre modelos (TFG)**:
> Debido a la diferencia de hardware entre desarrollo y evaluación, se utilizarán dos modelos distintos para la generación (LLM selector):
> - **Llama 3.1 8B**: Para uso en el equipo principal.
> - **Qwen 3.5 0.8B**: Para uso en los ordenadores del aula (menor capacidad).

## 1. Especificaciones de alto nivel

### 1.1 User stories
- US1: Como usuario, quiero cargar documentos para que la IA los use como contexto.
- US2: Como usuario, quiero hacer una pregunta y recibir una respuesta basada en los documentos guardados.
- US3: Como usuario, quiero poder seleccionar el modo de generación (RAG o Búsqueda Web) y el modelo a utilizar.
- US4: Como usuario, quiero que la interfaz sea conversacional (chat) en Reflex.

### 1.2 Criterios de aceptación (AC)
- AC1 (ingest): `POST /api/ingest` con archivos devuelve `status: indexed` y `chunks > 0`.
- AC2 (query): `POST /api/query` con `query` devuelve `answer` no vacío y `sources`.
- AC3 (relevancia): si top score >= threshold y el modo es RAG, `used_web=false`.
- AC4 (fallback/mode): si el selector está en modo web, se ignora RAG y `used_web=true`.
- AC5 (offline): si no hay internet o se fuerza modo local, el endpoint query sigue funcionando con datos locales y el modelo offline.


## 2. API Contract

### 2.1 POST /api/ingest
**Request**: multipart/form-data files[]
**Response**:
```json
{ "status": "indexed", "documents": [{"filename":"...","chunks": 8}], "indexed_chunks": 8 }
```

### 2.2 POST /api/query
**Request**:
```json
{
  "query": "¿Qué es RAG?",
  "top_k": 5,
  "mode": "rag", 
  "model": "llama-3.1-8b"
}
```
**Response**:
```json
{
  "answer": "RAG es...",
  "sources": ["doc1_chunk_2","doc5_chunk_1"],
  "scores": [0.92,0.88],
  "used_web": false
}
```

### 2.3 GET /api/stats
**Response**:
```json
{ "doc_count": 4, "chunk_count": 120, "index_size": "16MB" }
```

### 2.4 POST /api/index/clear
**Response**:
```json
{"status":"cleared"}
```

## 3. Data model y storage

### 3.1 Chunk entidad
- `chunk_id`: string
- `doc_id`: string
- `text`: string
- `embedding`: vector
- `metadata`: {source, start_token, end_token}

### 3.2 Persistencia
- FAISS index en `data/vector.index` (manejado por `backend/app/core/rag.py`)
- Mapeo chunk metadata en JSON (`data/chunks.json`) con `source` y `text`
- Documentos crudos guardados en `data/documents/`

## 4. Pipeline de implementación (Spec Driven)

### 4.1 Mínimo viable (MVP)
1. Endpoint ingest parsea texto y chunk.
2. Embeddings con `all-MiniLM-L6-v2`.
3. Indexado FAISS.
4. Query vec->top K.
5. Respuesta de placeholder (inicialmente) y `sources`.

### 4.2 Criterios de pasos
- Al ejecutar ingest, `data/chunks.json` se actualiza.
- Al ejecutar query, se busca top_k y se retorna `sources`.
- Al ejecutar query sin datos, retorna error 400 con mensaje.

## 5. Casos de prueba (también specs)

### 5.1 test_ingest
- Carga `tests/fixtures/notes.txt`.
- Espera `status=indexed`, `chunks >= 1`.

### 5.2 test_query_local
- Ejecuta `POST /api/query` con pregunta relacionada (modo rag).
- Espera `answer` no vacío, `used_web=false`.

### 5.3 test_query_web
- Ejecuta `POST /api/query` con `mode: web`.
- Espera `used_web=true` y `answer` no vacío.

### 5.4 test_offline
- Simular sin web; `mode: rag` con modelo local no debe explotar.

## 6. Configuración y run
- Dependencias separadas en `frontend/requirements.txt` y `backend/requirements.txt`.
- Variables de entorno `.env`: `CHUNK_SIZE`, `TOP_K`, `THRESHOLD`, etc.
- Entorno virtual global: `.venv/`

**Para arrancar toda la aplicación (Front + Back):**
- Ejecutar el script: `.\scripts\start-dev.bat`

## 7. Prioridades de fase 2
1. Mejorar chunking (longitud adaptativa, semántica)
2. Integrar `llama-cpp-python` para generación real
3. UI Reflex chat + streaming
4. Autenticación local (opcional)

EOF
