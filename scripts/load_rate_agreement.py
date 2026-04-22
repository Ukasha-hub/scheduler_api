import re
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.rate_agreement import RateAgreement
from datetime import datetime


def parse_sql_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    inserts = re.findall(r"INSERT INTO `?rate_agreement`?.*?VALUES\s*(.*?);", content, re.S)

    rows = []
    for block in inserts:
        values = re.findall(r"\((.*?)\)", block, re.S)
        for v in values:
            # split carefully (handles strings)
            parts = re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", v)
            rows.append([p.strip().strip("'") for p in parts])

    return rows


def convert_row(row):
    def clean_datetime(val):
        if val in ("0000-00-00 00:00:00", "NULL", "", None):
            return None
        return val
    def safe_datetime(val):
        cleaned = clean_datetime(val)
        return cleaned if cleaned else datetime(1970, 1, 1)

    return {
        "rate_agreementNo": int(row[1]),
        "agent_code": row[2],
        "agent_name": row[3],
        "startDate": clean_datetime(row[4]),
        "endDate": clean_datetime(row[5]),
        "approveDate": clean_datetime(row[6]),
        "rate_agreementLine_ID": int(row[7]),
        "timeslot": row[8],
        "positionName": row[9] or None,
        "priority": row[10] or None,
        "program": row[11] or None,
        "timeBand": row[12] or None,
        "rate": float(row[13]),
        "adType": row[14],
        "episode_no": int(row[15]),
        "limit1": float(row[16]),
        "type": row[17],
        "lineStartDate": safe_datetime(row[18]),
        "lineEndDate": safe_datetime(row[19]),
    }


def load_data():
    db: Session = SessionLocal()

    rows = parse_sql_file("rate_agreement.sql")

    objects = []
    EXPECTED_COLUMNS = 20

    for r in rows:
        if len(r) != EXPECTED_COLUMNS:
            print(f"❌ Skipping bad row (len={len(r)}):", r[:5])
            continue

        data = convert_row(r)

        if data["lineStartDate"] is None or data["lineEndDate"] is None:
            print("❌ Missing dates:", r[:5])
            continue

        obj = RateAgreement(**data)
        objects.append(obj)

    db.bulk_save_objects(objects)
    db.commit()
    db.close()

    print(f"Inserted {len(objects)} rows!")


if __name__ == "__main__":
    load_data()