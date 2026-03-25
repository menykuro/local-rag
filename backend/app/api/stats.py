from fastapi import APIRouter
from app.core import rag

router = APIRouter()

@router.get('')
async def get_stats():
    return rag.instance.get_stats()
