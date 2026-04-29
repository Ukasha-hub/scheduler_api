from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.utils.logger import log_action
from typing import List, Dict
from app.services.storage.db_lock import execute_with_table_lock
from sqlalchemy import Date
import asyncio
import json
from datetime import date, timedelta, datetime

from app.db.session import get_db
from app.models.scheduler import Scheduler
from app.schemas.scheduler import (
    SchedulerCreate,
    SchedulerRead,
    SchedulerUpdate,
    SchedulerBulkDelete,
    SchedulerSync,
    SchedulerReorderRequest
)

router = APIRouter()

# Simple in-memory lock storage
edit_lock = {
    "locked": False,
    "locked_at": None,
    "lock_timeout_seconds": 30
}
lock_timeout_seconds = 30

@router.post("/lock/acquire")
async def acquire_lock():
    """Acquire a lock for editing the schedule"""
    global edit_lock
    
    current_time = datetime.now()
    
    # Check if lock exists and is still valid
    if edit_lock["locked"]:
        lock_age = (current_time - edit_lock["locked_at"]).total_seconds()
        if lock_age < lock_timeout_seconds:
            # Lock is still valid, cannot acquire
            await sse_manager.broadcast("lock_denied", {
                "locked": True,
                "remaining_seconds": int(lock_timeout_seconds - lock_age)
            }, None)
            return {"acquired": False, "message": "Schedule is currently locked"}
    
    # Acquire the lock
    edit_lock = {
        "locked": True,
        "locked_at": current_time,
        "lock_timeout_seconds": lock_timeout_seconds
    }
    
    # Broadcast lock acquired to all clients
    await sse_manager.broadcast("lock_acquired", {
        "locked": True
    }, None)
    
    return {"acquired": True}

@router.post("/lock/release")
async def release_lock():
    """Release the edit lock"""
    global edit_lock
    
    edit_lock = {
        "locked": False,
        "locked_at": None,
        "lock_timeout_seconds": 30
    }
    
    # Broadcast lock released to all clients
    await sse_manager.broadcast("lock_released", {
        "locked": False
    }, None)
    
    return {"released": True}

@router.get("/lock/status")
async def get_lock_status():
    """Get current lock status"""
    global edit_lock
    
    if edit_lock["locked"]:
        lock_age = (datetime.now() - edit_lock["locked_at"]).total_seconds()
        if lock_age >= lock_timeout_seconds:
            # Lock expired, auto-release
            edit_lock["locked"] = False
            edit_lock["locked_at"] = None
            return {"locked": False}
        
        return {
            "locked": True,
            "remaining_seconds": int(lock_timeout_seconds - lock_age)
        }
    
    return {"locked": False}

@router.post("/lock/heartbeat")
async def lock_heartbeat():
    """Refresh the lock to prevent timeout"""
    global edit_lock
    
    if edit_lock["locked"]:
        # Refresh the lock timestamp
        edit_lock["locked_at"] = datetime.now()
        return {"refreshed": True}
    
    return {"refreshed": False}

# SSE event manager to track connected clients
class SSEEventManager:
    def __init__(self):
        self.clients: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()
    
    async def connect(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        async with self._lock:
            self.clients.append(queue)
            print(f"✅ Client connected. Total clients: {len(self.clients)}")
        return queue
    
    async def disconnect(self, queue: asyncio.Queue):
        async with self._lock:
            if queue in self.clients:
                self.clients.remove(queue)
                print(f"❌ Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast(self, event_type: str, data: Dict, date_filter: date = None):
        """Broadcast event to all connected clients"""
        async with self._lock:
            if not self.clients:
                print(f"⚠️ No clients connected, skipping broadcast for {event_type}")
                return
            
            # IMPORTANT: Always include the date in the message
            message = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "date": date_filter.isoformat() if date_filter else None
            }
            
            print(f"📡 Broadcasting {event_type} to {len(self.clients)} clients")
            print(f"   Message: {message}")
            
            disconnected = []
            for queue in self.clients:
                try:
                    await queue.put(message)
                except Exception as e:
                    print(f"Error sending to client: {e}")
                    disconnected.append(queue)
            
            # Clean up disconnected clients
            for queue in disconnected:
                if queue in self.clients:
                    self.clients.remove(queue)

# Global SSE manager instance
sse_manager = SSEEventManager()

# IMPORTANT: Put the SSE endpoint BEFORE the regular GET endpoint
# to avoid route conflicts
@router.get("/sse/events")
async def sse_events(request: Request, date: date = None):
    """SSE endpoint for real-time updates"""
    async def event_generator():
        queue = await sse_manager.connect()
        try:
            while True:
                try:
                    # Wait for message with timeout to check client connection
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    print(f"📨 Sending message: {message.get('type')} for date {message.get('date')}")
                    
                    # CRITICAL FIX: Send ALL messages, let client filter by date
                    # This ensures all connected clients get updates regardless of their date filter
                    # Remove the date filter entirely to broadcast to ALL clients
                    yield f"data: {json.dumps(message)}\n\n"
                    
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            await sse_manager.disconnect(queue)
            raise
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
    

@router.get("/", response_model=List[SchedulerRead])
def list_schedulers(
    date: date,
    include_soft_deleted: bool = Query(False, description="Include rows with duration 00:00:00:00"),
    db: Session = Depends(get_db)
):
    query = db.query(Scheduler).filter(Scheduler.start_date.cast(Date) == date)
    
    # Filter out soft-deleted rows (duration = "00:00:00:00") unless explicitly requested
    if not include_soft_deleted:
        query = query.filter(Scheduler.duration != "00:00:00:00")
    
    return query.order_by(Scheduler.start_date).all()

@router.get("/{scheduler_id}", response_model=SchedulerRead)
def get_scheduler(scheduler_id: int, db: Session = Depends(get_db)):
    obj = db.query(Scheduler).filter(Scheduler.id == scheduler_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Scheduler not found")
    return obj

@router.post("/", response_model=SchedulerRead)
async def create_scheduler(  # Make async
    payload: SchedulerCreate,
    emp_id: str = Query(...),
    db: Session = Depends(get_db)
):
    obj = Scheduler(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    log_action(
        db,
        emp_id=emp_id,
        action=f"Created scheduler row {obj.id}"
    )
    
    # Direct async broadcast (no threading needed since endpoint is async)
    await sse_manager.broadcast(
        "scheduler_created",
        {
            "id": obj.id, 
            "table_id": obj.table_id, 
            "program": obj.program, 
            "type": obj.type,
            "start_date": obj.start_date.isoformat() if obj.start_date else None
        },
        obj.start_date.date() if obj.start_date else None
    )

    return obj

@router.post("/sync", response_model=List[SchedulerRead])
async def sync_day_scheduler(  # Make this async
    date: date,
    rows: List[SchedulerCreate],
    emp_id: str = Query(...),
    action: str = Query(None),
    db: Session = Depends(get_db)
):
    def operation():
        existing = {
            s.table_id: s
            for s in db.query(Scheduler)
            .filter(Scheduler.start_date.cast(Date) == date)
            .all()
        }

        incoming_ids = set()
        changed_table_ids = set()

        for row in rows:
            if not hasattr(row, "table_id"):
                continue

            incoming_ids.add(row.table_id)

            if row.table_id in existing:
                obj = existing[row.table_id]
                # Check if any field changed
                for field, value in row.model_dump().items():
                    if getattr(obj, field) != value:
                        changed_table_ids.add(row.table_id)
                        break
                for field, value in row.model_dump().items():
                    setattr(obj, field, value)
            else:
                obj = Scheduler(**row.model_dump())
                db.add(obj)
                changed_table_ids.add(row.table_id)

        for table_id, obj in existing.items():
            if table_id not in incoming_ids:
                db.delete(obj)
                changed_table_ids.add(table_id)

        db.flush()

        log_action(
            db,
            emp_id=emp_id,
            action=action
        )
        
        updated_rows = (
            db.query(Scheduler)
            .filter(Scheduler.start_date.cast(Date) == date)
            .order_by(Scheduler.start_date)
            .all()
        )
        
        return updated_rows, changed_table_ids

    # Execute the operation with lock
    updated_rows, changed_table_ids = execute_with_table_lock(
        db=db,
        table_name="scheduler",
        operation=operation,
    )
    
    # Broadcast AFTER the operation is complete and lock is released
    await sse_manager.broadcast(
        "scheduler_synced",
        {
            "date": date.isoformat(),
            "changed_ids": list(changed_table_ids),
            "action": action,
            "row_count": len(updated_rows)
        },
        date
    )
    
    return updated_rows
  

@router.put("/{table_id}", response_model=SchedulerRead)
def update_scheduler_by_table_id(
    table_id: int,
    payload: SchedulerUpdate,
    emp_id: str = Query(...),
    db: Session = Depends(get_db),
):
    def operation():
        obj = db.query(Scheduler).filter(Scheduler.table_id == table_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail="Scheduler not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)

        db.flush()

        log_action(
            db,
            emp_id=emp_id,
            action=f"Updated scheduler {table_id}"
        )
        
        # Broadcast the update in a thread
        import threading
        def broadcast_in_thread():
            asyncio.run(sse_manager.broadcast(
                "scheduler_updated",
                {
                    "table_id": table_id,
                    "changes": payload.model_dump(exclude_unset=True),
                    "data": {
                        "table_id": obj.table_id,
                        "program": obj.program,
                        "type": obj.type,
                        "duration": obj.duration,
                        "start_date": obj.start_date.isoformat() if obj.start_date else None,
                        "end_date": obj.end_date.isoformat() if obj.end_date else None,
                    }
                },
                obj.start_date.date() if obj.start_date else None
            ))
        
        thread = threading.Thread(target=broadcast_in_thread)
        thread.start()

        return obj

    return execute_with_table_lock(
        db=db,
        table_name="scheduler",
        operation=operation,
    )

@router.delete("/{table_id}")
def delete_scheduler_by_table_id(
    table_id: int,
    db: Session = Depends(get_db)
):
    def operation():
        obj = db.query(Scheduler).filter(Scheduler.table_id == table_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail="Scheduler not found")
        
        row_date = obj.start_date.date() if obj.start_date else None

        db.delete(obj)
        db.flush()
        
        # Broadcast the deletion in a thread
        import threading
        def broadcast_in_thread():
            asyncio.run(sse_manager.broadcast(
                "scheduler_deleted",
                {
                    "table_id": table_id,
                    "date": row_date.isoformat() if row_date else None
                },
                row_date
            ))
        
        thread = threading.Thread(target=broadcast_in_thread)
        thread.start()

        return {"success": True}

    return execute_with_table_lock(
        db=db,
        table_name="scheduler",
        operation=operation,
    )

# Add this new endpoint for soft delete
@router.delete("/soft/{table_id}")
def soft_delete_scheduler_by_table_id(
    table_id: int,
    emp_id: str = Query(...),
    action: str = Query(None),
    db: Session = Depends(get_db)
):
    """Soft delete a row by setting duration to 00:00:00:00"""
    def operation():
        obj = db.query(Scheduler).filter(Scheduler.table_id == table_id).first()
        if not obj:
            raise HTTPException(status_code=404, detail="Scheduler not found")
        
        # Set duration to 00:00:00:00 instead of deleting
        obj.duration = "00:00:00:00"
        db.flush()
        
        row_date = obj.start_date.date() if obj.start_date else None

        log_action(
            db,
            emp_id=emp_id,
            action=action or f"Soft deleted scheduler {table_id}"
        )
        
        # Broadcast the soft deletion
        import threading
        def broadcast_in_thread():
            asyncio.run(sse_manager.broadcast(
                "scheduler_soft_deleted",
                {
                    "table_id": table_id,
                    "date": row_date.isoformat() if row_date else None
                },
                row_date
            ))
        
        thread = threading.Thread(target=broadcast_in_thread)
        thread.start()

        return {"success": True, "soft_deleted": True, "table_id": table_id}

    return execute_with_table_lock(
        db=db,
        table_name="scheduler",
        operation=operation,
    )