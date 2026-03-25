from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    project_name: str = 'local-rag'
    embedding_model: str = 'all-MiniLM-L6-v2'
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    relevance_threshold: float = 0.7
    default_mode: str = 'rag'
    default_model: str = 'llama-3.1-8b'

settings = Settings()
