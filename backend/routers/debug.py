from fastapi import APIRouter
from ..services import data_service

router = APIRouter()

@router.get("/debug_entity/{entity_id}")
def debug_entity(entity_id: str):
    return data_service.data_service.get_entity(entity_id)
