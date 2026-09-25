from fastapi import APIRouter, HTTPException, Query
from ..models.schemas import EntityResponse, NeighborhoodResponse
from ..services import data_service

router = APIRouter(prefix="/entities", tags=["Entities"])

# IMPORTANT: /clusters must be BEFORE /{entity_id} to avoid route shadowing
@router.get("/clusters")
def get_clusters():
    """
    Get identified suspicious clusters.
    Advanced clustering is not implemented in the MVP.
    """
    return []

@router.get("/{entity_id}", response_model=EntityResponse)
def get_entity(entity_id: str):
    """
    Get details for a specific entity (wallet, IP, or transaction).
    """
    if data_service.data_service is None:
        raise HTTPException(status_code=500, detail="Data service not initialized")
        
    entity = data_service.data_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    return entity

@router.get("/{entity_id}/neighborhood", response_model=NeighborhoodResponse)
def get_entity_neighborhood(entity_id: str, depth: int = Query(1, ge=1, le=3)):
    """
    Get the local graph neighborhood for an entity.
    """
    if data_service.data_service is None:
        raise HTTPException(status_code=500, detail="Data service not initialized")
        
    neighborhood = data_service.data_service.get_entity_neighborhood(entity_id, depth)
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Entity neighborhood not found")
        
    return neighborhood
