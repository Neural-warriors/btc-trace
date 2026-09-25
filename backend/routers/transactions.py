from fastapi import APIRouter, HTTPException
from ..models.schemas import TransactionResponse
from ..services import data_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/{txid}", response_model=TransactionResponse)
def get_transaction(txid: str):
    """
    Get details for a specific transaction.
    """
    if data_service.data_service is None:
        raise HTTPException(status_code=500, detail="Data service not initialized")
        
    transaction = data_service.data_service.get_transaction(txid)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    return transaction
