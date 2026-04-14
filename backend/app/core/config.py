import os
from pydantic_settings import BaseSettings

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class Settings(BaseSettings):
    project_name: str = 'local-rag'
    embedding_model: str = 'all-MiniLM-L6-v2'
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    relevance_threshold: float = 0.7
    default_mode: str = 'rag'
    default_model: str = 'llama-3.1-8b'
    llm_model_path: str = os.path.join(PROJECT_ROOT, 'data', 'models', 'Qwen3.5-0.8B-BF16.gguf')
    llm_context_window: int = 4096
    llm_max_tokens: int = 512

settings = Settings()
