# app/api/v1/endpoints/package.py

from fastapi import APIRouter, Depends,  Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.package import Package
from app.schemas.package import PackageCreate, PackageRead
from app.schemas.package import PackagePatch
from fastapi import HTTPException
import json
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import JSON
from app.utils.logger import log_action
from app.services.storage.db_lock import execute_with_table_lock
import time


router = APIRouter()

def normalize_items(items: list[dict]) -> list[dict]:
    normalized = []

    for item in items:
        if "id" in item:
            item = {**item, "id": str(item["id"])}
        normalized.append(item)

    return normalized

# Get all packages
@router.get("/", response_model=list[PackageRead])
def get_packages(db: Session = Depends(get_db)):
    return db.query(Package).all()


# Create or Update package
@router.post("/", response_model=PackageRead)
def save_package(payload: PackageCreate, emp_id: str = Query(...), db: Session = Depends(get_db)):
    def operation():
        pkg = db.query(Package).filter(Package.name == payload.name).first()

        if pkg:
            # Update: append new items without duplicates
            existing_ids = {item["id"] for item in pkg.items}
            new_items = [item for item in payload.items if item["id"] not in existing_ids]
            pkg.items.extend(new_items)
            db.flush()
            log_action(db, emp_id=emp_id, action=f"Appended items {new_items} to package {pkg.name}")
            return pkg

        # Create new package
        new_pkg = Package(
            name=payload.name,
            items=normalize_items(payload.items)
        )
        db.add(new_pkg)
        db.flush()
        log_action(db, emp_id=emp_id, action=f"Created package {payload.name} with items {payload.items}")
        return new_pkg

    return execute_with_table_lock(
        db=db,
        table_name="packages",
        operation=operation,
    )

@router.patch("/{package_id}", response_model=PackageRead)
def update_package(package_id: int, payload: PackagePatch, emp_id: str = Query(...), db: Session = Depends(get_db)):
    def operation():
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            raise HTTPException(status_code=404, detail="Package not found")

        updated_fields = []

        if payload.name is not None:
            updated_fields.append(f"name: {pkg.name} → {payload.name}")
            pkg.name = payload.name

        if payload.items is not None:
            if pkg.items is None:
                pkg.items = []

            existing_ids = {item["id"] for item in pkg.items}
            incoming_items = normalize_items(payload.items)
            new_items = [item for item in incoming_items if item["id"] not in existing_ids]
            pkg.items = pkg.items + new_items
            if new_items:
                updated_fields.append(f"Added items: {new_items}")

        db.flush()

        log_action(db, emp_id=emp_id, action=f"Updated package {pkg.name}: {', '.join(updated_fields)}")
        return pkg

    return execute_with_table_lock(
        db=db,
        table_name="packages",
        operation=operation,
    )

@router.delete("/{package_id}/item/{item_id}", response_model=PackageRead)
def delete_package_item(package_id: int, item_id: str, emp_id: str = Query(...), db: Session = Depends(get_db)):
    def operation():
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            raise HTTPException(status_code=404, detail="Package not found")

        if not pkg.items:
            raise HTTPException(status_code=400, detail="No items in package")

        new_items = [item for item in pkg.items if item["id"] != item_id]
        if len(new_items) == len(pkg.items):
            raise HTTPException(status_code=404, detail="Item not found in package")

        pkg.items = new_items
        db.flush()
        log_action(db, emp_id=emp_id, action=f"Deleted item {item_id} from package {pkg.name}")
        return pkg

    return execute_with_table_lock(
        db=db,
        table_name="packages",
        operation=operation,
    )

@router.delete("/{package_id}", response_model=dict)
def delete_package(package_id: int, emp_id: str = Query(...), db: Session = Depends(get_db)):
    def operation():
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            raise HTTPException(status_code=404, detail="Package not found")

        db.delete(pkg)
        db.flush()
        log_action(db, emp_id=emp_id, action=f"Deleted package {pkg.name}")
        return {"message": "Package deleted successfully", "id": package_id}

    return execute_with_table_lock(
        db=db,
        table_name="packages",
        operation=operation,
    )