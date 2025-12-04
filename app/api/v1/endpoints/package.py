# app/api/v1/endpoints/package.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.package import Package
from app.schemas.package import PackageCreate, PackageRead
from app.schemas.package import PackagePatch
from fastapi import HTTPException
import json
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import JSON

router = APIRouter()

# Get all packages
@router.get("/", response_model=list[PackageRead])
def get_packages(db: Session = Depends(get_db)):
    return db.query(Package).all()


# Create or Update package
@router.post("/", response_model=PackageRead)
def save_package(payload: PackageCreate, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter(Package.name == payload.name).first()

    if pkg:
        # Update: append new items without duplicates
        existing_ids = {item["id"] for item in pkg.items}
        new_items = [item for item in payload.items if item["id"] not in existing_ids]
        pkg.items.extend(new_items)
        db.commit()
        db.refresh(pkg)
        return pkg

    # Create new package
    new_pkg = Package(
        name=payload.name,
        items=payload.items
    )
    db.add(new_pkg)
    db.commit()
    db.refresh(new_pkg)
    return new_pkg


@router.patch("/{package_id}", response_model=PackageRead)
def update_package(package_id: int, payload: PackagePatch, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter(Package.id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    if payload.name is not None:
        pkg.name = payload.name

    if payload.items is not None:
        # ensure pkg.items is a list
        if pkg.items is None:
            pkg.items = []

        # Avoid duplicates
        existing_ids = {item["id"] for item in pkg.items}
        new_items = [item for item in payload.items if item["id"] not in existing_ids]

        # Assign a new list to trigger SQLAlchemy change tracking
        pkg.items = pkg.items + new_items

    db.commit()
    db.refresh(pkg)
    return pkg

@router.delete("/{package_id}/item/{item_id}", response_model=PackageRead)
def delete_package_item(package_id: int, item_id: str, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter(Package.id == package_id).first()

    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    if not pkg.items:
        raise HTTPException(status_code=400, detail="No items in package")

    new_items = [item for item in pkg.items if item["id"] != item_id]

    if len(new_items) == len(pkg.items):
        raise HTTPException(status_code=404, detail="Item not found in package")

    pkg.items = new_items  # trigger change tracking

    db.commit()
    db.refresh(pkg)
    return pkg

@router.delete("/{package_id}", response_model=dict)
def delete_package(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter(Package.id == package_id).first()

    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    db.delete(pkg)
    db.commit()

    return {"message": "Package deleted successfully", "id": package_id}