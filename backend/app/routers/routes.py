from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app import database, models, schemas

router = APIRouter(
    prefix="/routes",
    tags=["Routes"]
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.Route)
def create_route(
    route: schemas.RouteCreate,
    db: Session = Depends(get_db)
):
    db_route = models.Route(**route.dict())
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


@router.get("/", response_model=List[schemas.Route])
def read_routes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Route)
        .offset(skip)
        .limit(limit)
        .all()
    )
