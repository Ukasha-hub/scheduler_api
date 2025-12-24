from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.slug import Slug
from app.schemas.slug import SlugCreate, SlugRead, SlugUpdate
from app.utils.logger import log_action

router = APIRouter()

# -----------------------------
# GET ALL
# -----------------------------
@router.get("/", response_model=list[SlugRead])
def get_all_slugs(db: Session = Depends(get_db)):
    items = db.query(Slug).all()
    return items

# -----------------------------
# CREATE
# -----------------------------
@router.post("/", response_model=SlugRead)
def create_slug(payload: SlugCreate, db: Session = Depends(get_db)):
    new = Slug(
        programe_name=payload.programe_name,
        slug=payload.slug,
        slug_repeat=payload.slug_repeat
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    log_action(db, emp_id="101", action=f"Created new slug, name: {payload.programe_name}, slug:{payload.slug}, slug_repeat:{payload.slug_repeat}")
    return new

# -----------------------------
# UPDATE BY ID
# -----------------------------
@router.put("/{id}", response_model=SlugRead)
def update_slug(id: int, payload: SlugUpdate, db: Session = Depends(get_db)):
    item = db.query(Slug).filter(Slug.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Slug not found")

    item.programe_name= payload.programe_name
    item.slug  = payload.slug 
    item.slug_repeat = payload.slug_repeat

    db.commit()
    db.refresh(item)
    log_action(db, emp_id="101", action=f"Updated slug to name: {payload.programe_name}, slug:{payload.slug}, slug_repeat:{payload.slug_repeat}")
    return item

# -----------------------------
# DELETE BY ID
# -----------------------------
@router.delete("/{id}")
def delete_slug(id: int, db: Session = Depends(get_db)):
    item = db.query(Slug).filter(Slug.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Slug not found")

    db.delete(item)
    db.commit()
    log_action(db, emp_id="101", action=f"Deleted programme name: {item.programe_name}")
    return {"detail": "Deleted successfully"}
