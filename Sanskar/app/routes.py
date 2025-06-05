from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import CutoffOut
from app.crud import get_top_colleges

router = APIRouter()

@router.get("/recommend", response_model=list[CutoffOut])
def recommend_colleges(
    rank: int = Query(...),
    caste: str = Query(...),
    gender: str = Query(...),
    db: Session = Depends(get_db)
):
    return get_top_colleges(db, rank, caste, gender)
