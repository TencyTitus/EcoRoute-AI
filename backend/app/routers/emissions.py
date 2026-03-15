from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import database, models, schemas
from datetime import datetime
from typing import List

router = APIRouter(prefix="/emissions", tags=["Emissions"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.EmissionLog)
def create_emission_log(log: schemas.EmissionLogCreate, db: Session = Depends(get_db)):
    db_log = models.EmissionLog(**log.dict(), recorded_at=datetime.now())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


@router.get("/", response_model=List[schemas.EmissionLog])
def read_emission_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.EmissionLog).offset(skip).limit(limit).all()
