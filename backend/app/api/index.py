from fastapi import APIRouter
from app.core import rag

router = APIRouter()

@router.post('/clear')
async def clear_index():
    rag.instance.clear()
    return {"status": "cleared"}
