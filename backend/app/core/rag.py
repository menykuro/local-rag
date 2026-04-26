import os
import json
import faiss
import numpy as np
import logging
from sentence_transformers import SentenceTransformer
from app.core.config import settings, PROJECT_ROOT

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class RAGCore:
    def __init__(self):
        self.model = SentenceTransformer(settings.embedding_model)
        self.index_path = os.path.join(PROJECT_ROOT, 'data', 'vector.index')
        self.chunks_path = os.path.join(PROJECT_ROOT, 'data', 'chunks.json')
        # Embeeded size typically 384 for all-MiniLM-L6-v2
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.chunks_meta = []
        self._load_data()
        
        self.llm = None
        if Llama is not None:
            try:
                self.llm = Llama(
                    model_path=settings.llm_model_path,
                    n_ctx=settings.llm_context_window,
                    verbose=False
                )
            except Exception as e:
                logging.error(f"Error cargando LLM: {e}")

    def _load_data(self):
        os.makedirs(os.path.join(PROJECT_ROOT, 'data'), exist_ok=True)
        if os.path.exists(self.chunks_path):
            with open(self.chunks_path, 'r', encoding='utf-8') as f:
                self.chunks_meta = json.load(f)
        else:
            self.chunks_meta = []

        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            self.index = faiss.IndexFlatL2(self.embedding_dim)

    def _save_data(self):
        with open(self.chunks_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks_meta, f, ensure_ascii=False, indent=2)
        faiss.write_index(self.index, self.index_path)

    def add_documents(self, chunks: list, source: str):
        if not chunks:
            return
            
        embeddings = self.model.encode(chunks)
        
        # Add to faiss
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Add meta
        for chunk in chunks:
            self.chunks_meta.append({
                'source': source,
                'text': chunk
            })
            
        self._save_data()

    def search(self, query: str, top_k: int = 5):
        if self.index.ntotal == 0:
            return [], []

        query_emb = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_emb).astype('float32'), top_k)
        
        results = []
        scores = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.chunks_meta):
                results.append(self.chunks_meta[idx])
                # Convertir L2 distance a Cosine Similarity (asumiendo embeddings normalizados)
                # L2^2 = 2 - 2 * cos_sim => cos_sim = 1 - L2^2 / 2
                score = float(1.0 - (distances[0][i] / 2.0))
                scores.append(score)
                
        return results, scores
        
    def _build_messages(self, query: str, context: str, is_fallback: bool, is_web_fallback: bool, history: list = None) -> list:
        """Construye la lista de mensajes para el LLM con los prompts adecuados según el modo."""
        # Presupuesto de contexto: n_ctx - max_tokens - 200 overhead (~3 chars/token)
        max_context_tokens = settings.llm_context_window - settings.llm_max_tokens - 200
        max_context_chars = max(500, max_context_tokens * 3)

        if len(context) > max_context_chars:
            context = context[:max_context_chars] + "\n[...contexto recortado por límite de ventana...]"

        if is_web_fallback:
            if context.strip():
                system_prompt = (
                    "Eres JARVIS, un analista experto. Se ha realizado una búsqueda en internet para responder a esta pregunta.\n"
                    "REGLAS ESTRICTAS:\n"
                    "1. Responde basándote ÚNICAMENTE en los resultados de la web proporcionados.\n"
                    "2. Si los resultados de la web NO contienen el dato exacto (por ejemplo, piden la temperatura actual y solo ves la máxima/mínima), NO LO INVENTES. Di explícitamente qué datos has encontrado y confiesa que falta el dato exacto.\n"
                    "3. Menciona siempre que tu respuesta se basa en la búsqueda web reciente."
                )
            else:
                system_prompt = (
                    "Eres JARVIS. La búsqueda en internet ha fallado o ha sido bloqueada.\n"
                    "REGLAS ESTRICTAS:\n"
                    "1. Si la pregunta pide datos en tiempo real (clima, temperatura, hora actual, bolsa, noticias de hoy), TIENES PROHIBIDO INVENTAR LA RESPUESTA.\n"
                    "2. DEBES RESPONDER EXACTAMENTE ESTO: 'No puedo proporcionar el dato porque la búsqueda en internet ha fallado temporalmente y no tengo acceso a datos en tiempo real.'\n"
                    "3. Si la pregunta es sobre conocimiento general atemporal (historia, ciencia), responde usando tu conocimiento."
                )
            user_prompt = f"Resultados de la web:\n{context}\n\nPregunta actual: {query}\n\nRespuesta estructurada:"
        elif is_fallback:
            system_prompt = (
                "Eres JARVIS, un asistente experto. Estás funcionando sin conexión a internet.\n"
                "REGLAS ESTRICTAS:\n"
                "1. Si la pregunta requiere información en tiempo real (clima actual, temperatura, bolsa, noticias de hoy), TIENES PROHIBIDO INVENTAR LA RESPUESTA.\n"
                "2. DEBES RESPONDER: 'No tengo acceso a internet para buscar datos en tiempo real. Por favor, activa la búsqueda web.'\n"
                "3. Para preguntas de conocimiento atemporal, responde normalmente."
            )
            user_prompt = f"Pregunta actual: {query}\n\nRespuesta:"
        else:
            system_prompt = (
                "Eres un analista experto. Responde basándote estrictamente en el contexto proporcionado. "
                "Ignora mensajes anteriores del historial si no tienen relación con la pregunta actual. No inventes."
            )
            user_prompt = f"Contexto de documentos:\n{context}\n\nPregunta actual: {query}\n\nRespuesta estructurada:"

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def generate_answer(self, query: str, context: str, is_fallback: bool = False, is_web_fallback: bool = False, history: list = None) -> str:
        if self.llm is None:
            return f"[Modo Degradado - LLM no cargado]\nBasado en el contexto:\n{context[:200]}...\nRespuesta para: {query}"

        messages = self._build_messages(query, context, is_fallback, is_web_fallback, history)

        try:
            response = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=settings.llm_max_tokens,
                temperature=0.45
            )
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"[Error generando respuesta del LLM]: {str(e)}"

    def generate_answer_stream(self, query: str, context: str, is_fallback: bool = False, is_web_fallback: bool = False, history: list = None):
        """Generador que emite tokens uno a uno para streaming SSE."""
        if self.llm is None:
            yield "[Modo Degradado - LLM no cargado]"
            return

        messages = self._build_messages(query, context, is_fallback, is_web_fallback, history)

        try:
            stream = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=settings.llm_max_tokens,
                temperature=0.45,
                stream=True
            )
            for chunk in stream:
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                token = delta.get("content", "")
                if token:
                    yield token
        except Exception as e:
            yield f"[Error generando respuesta]: {str(e)}"
        
    def list_documents(self) -> list[dict]:
        """Devuelve la lista de documentos únicos con su número de chunks."""
        from collections import Counter
        counts = Counter(c["source"] for c in self.chunks_meta)
        return [{"source": src, "chunks": n} for src, n in counts.items()]

    def delete_document(self, source: str) -> bool:
        """Elimina un documento del índice por nombre de fuente.
        Reconstruye FAISS extrayendo los vectores existentes para evitar re-procesar con IA."""
        keep_indices = [i for i, c in enumerate(self.chunks_meta) if c["source"] != source]
        
        if len(keep_indices) == len(self.chunks_meta):
            return False  # No se encontró el documento

        # Extraer todos los vectores actuales antes de limpiar el índice
        if self.index.ntotal > 0:
            all_vectors = self.index.reconstruct_n(0, self.index.ntotal)
            filtered_vectors = all_vectors[keep_indices]
        else:
            filtered_vectors = np.array([])

        # Filtrar los metadatos
        self.chunks_meta = [self.chunks_meta[i] for i in keep_indices]

        # Reconstruir el índice FAISS con los vectores filtrados
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        if len(filtered_vectors) > 0:
            self.index.add(filtered_vectors)

        self._save_data()
        return True

    def get_stats(self):
        return {
            "doc_count": len(set(c["source"] for c in self.chunks_meta)),
            "chunk_count": len(self.chunks_meta),
            "index_size": f"{os.path.getsize(self.index_path) // 1024}KB" if os.path.exists(self.index_path) else "0KB"
        }
        
    def clear(self):
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.chunks_meta = []
        self._save_data()

instance = RAGCore()

