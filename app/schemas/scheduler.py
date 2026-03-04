from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Dict


class SchedulerBase(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    type: Optional[str] = None
    program: Optional[str] = None
    format: Optional[str] = None
    remark: Optional[str] = None
    rec_type: Optional[str] = None

    event_length: Optional[int] = None
    event_pid: Optional[int] = None

    order_ref: Optional[str] = None
    bp_code: Optional[str] = None

    duration: Optional[str] = None
    sframe: Optional[int] = None
    dframe: Optional[int] = None
    eframe: Optional[int] = None

    episode: Optional[str] = None
    segment: Optional[str] = None
    serial_type: Optional[str] = None
    asset: Optional[str] = None
    input_type: Optional[str] = None

    created: Optional[datetime] = None
    createdby: Optional[str] = None
    updated: Optional[datetime] = None
    updatedby: Optional[str] = None

    invoiced: Optional[bool] = None
    rate_agreement: Optional[int] = None
    rateAgreement_Line: Optional[int] = None

    ordered: Optional[bool] = None
    invoice_no: Optional[str] = None
    rateValidated: Optional[bool] = None

    slug_name: Optional[str] = None
    prev_time_period: Optional[Dict] = None
    time_period: Optional[Dict] = None
    table_id: int


class SchedulerCreate(SchedulerBase):
    pass


class SchedulerUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    type: Optional[str] = None
    program: Optional[str] = None
    format: Optional[str] = None
    remark: Optional[str] = None
    rec_type: Optional[str] = None

    event_length: Optional[int] = None
    event_pid: Optional[int] = None

    order_ref: Optional[str] = None
    bp_code: Optional[str] = None

    duration: Optional[str] = None
    sframe: Optional[int] = None
    dframe: Optional[int] = None
    eframe: Optional[int] = None

    episode: Optional[str] = None
    segment: Optional[str] = None
    serial_type: Optional[str] = None
    asset: Optional[str] = None
    input_type: Optional[str] = None

    created: Optional[datetime] = None
    createdby: Optional[str] = None
    updated: Optional[datetime] = None
    updatedby: Optional[str] = None

    invoiced: Optional[bool] = None
    rate_agreement: Optional[int] = None
    rateAgreement_Line: Optional[int] = None

    ordered: Optional[bool] = None
    invoice_no: Optional[str] = None
    rateValidated: Optional[bool] = None

    slug_name: Optional[str] = None
    prev_time_period: Optional[Dict] = None
    time_period: Optional[Dict] = None
    table_id: int


class SchedulerRead(SchedulerBase):
    id: int

    class Config:
        from_attributes = True


class SchedulerBulkDelete(BaseModel):
    ids: List[int]


class SchedulerSync(BaseModel):
    id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration: Optional[str] = None


class SchedulerReorderRow(BaseModel):
    id: int
    duration: Optional[str] = None


class SchedulerReorderRequest(BaseModel):
    date: date
    start_date: Optional[datetime] = None
    rows: List[SchedulerReorderRow]
