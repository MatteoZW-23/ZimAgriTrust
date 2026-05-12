import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.listing import BuyerRequest, FarmerResponse
from app.models.user import User, UserRole
from app.schemas.listing import BuyerRequestCreate, BuyerRequestResponse, FarmerResponseCreate, FarmerResponseResponse
from app.schemas.transaction import OrderResponse
from app.services.marketplace_service import marketplace_core

router = APIRouter()


@router.post("", response_model=BuyerRequestResponse)
@router.post("/", response_model=BuyerRequestResponse, include_in_schema=False)
def create_request(
    payload: BuyerRequestCreate,
    db: Session = Depends(get_db),
    buyer: User = Depends(require_roles(UserRole.BUYER, UserRole.ADMIN)),
) -> BuyerRequest:
    """
    ZimAgritrust Spec: Buyer posts what they want.
    """
    return marketplace_core.create_buyer_request(db, buyer, payload)


@router.get("", response_model=list[BuyerRequestResponse])
@router.get("/", response_model=list[BuyerRequestResponse], include_in_schema=False)
def list_requests(db: Session = Depends(get_db)) -> list[BuyerRequest]:
    """
    Farmers browse active requests.
    """
    return db.query(BuyerRequest).filter(BuyerRequest.status == "open").all()


@router.get("/me", response_model=list[BuyerRequestResponse])
def list_my_requests(
    db: Session = Depends(get_db),
    buyer: User = Depends(require_roles(UserRole.BUYER, UserRole.ADMIN)),
) -> list[BuyerRequest]:
    query = db.query(BuyerRequest)
    if buyer.role != UserRole.ADMIN:
        query = query.filter(BuyerRequest.buyer_id == buyer.id)
    return query.order_by(BuyerRequest.created_at.desc()).all()


@router.delete("/{request_id}")
def delete_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    buyer: User = Depends(require_roles(UserRole.BUYER, UserRole.ADMIN)),
):
    request = db.query(BuyerRequest).filter(BuyerRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if request.buyer_id != buyer.id and buyer.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete this request")
    request.status = "cancelled"
    db.commit()
    return {"success": True}


@router.post("/{request_id}/respond", response_model=FarmerResponseResponse)
def respond_to_request(
    request_id: uuid.UUID,
    payload: FarmerResponseCreate,
    db: Session = Depends(get_db),
    farmer: User = Depends(require_roles(UserRole.FARMER)),
) -> FarmerResponse:
    """
    Farmers respond with supply capacity and bid price.
    """
    request = db.query(BuyerRequest).filter(BuyerRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return marketplace_core.farmer_respond_to_request(db, farmer, request, payload)


@router.post("/responses/{response_id}/accept", response_model=OrderResponse)
def accept_bid(
    response_id: uuid.UUID,
    db: Session = Depends(get_db),
    buyer: User = Depends(require_roles(UserRole.BUYER, UserRole.ADMIN)),
):
    """
    Buyer accepts a farmer's response, creating an order and initiating escrow.
    """
    response = db.query(FarmerResponse).filter(FarmerResponse.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Bid response not found")
    
    if response.request.buyer_id != buyer.id and buyer.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to accept this bid")

    return marketplace_core.accept_farmer_response(db, response)
