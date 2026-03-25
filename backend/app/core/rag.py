import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings

class RAGCore:
    def __init__(self):
        self.model = SentenceTransformer(settings.embedding_model)
        self.index_path = 'data/vector.index'
        self.chunks_path = 'data/chunks.json'
        # Embeeded size typically 384 for all-MiniLM-L6-v2
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.chunks_meta = []
        self._load_data()

    def _load_data(self):
        os.makedirs('data', exist_ok=True)
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
                # Lower L2 distance is better. Convert distance to a pseudo-score
                score = 1.0 / (1.0 + distances[0][i])
                scores.append(score)
                
        return results, scores
        
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
