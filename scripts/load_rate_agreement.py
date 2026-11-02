"""
load_rate_agreement.py

Robust loader for a phpMyAdmin / mysqldump SQL file into the
`rate_agreement` table via SQLAlchemy.

Fixes:
  * Correct MySQL string handling: backslash escapes (\', \\, \", \n, \r,
    \t, \0, \Z, \b), doubled single quotes (''), and any quote char inside
    the other quote type.
  * Quote-aware scan for ';' and for ')', so values containing ');' or '),'
    don't truncate the row.
  * Treats unquoted NULL as Python None.
  * Reports skipped rows to `skipped_rows.tsv` so nothing is silently lost.
  * Bulk inserts in chunks; a bad row is logged and skipped, not fatal.
"""

import os
import re
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models.rate_agreement import RateAgreement


# ---------------------------------------------------------------------------
# MySQL dump parsing
# ---------------------------------------------------------------------------

# MySQL backslash escapes for string literals
_ESCAPE_MAP = {
    "0": "\0",
    "b": "\b",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "Z": "\x1a",   # Ctrl-Z
    "\\": "\\",
    "'": "'",
    '"': '"',
}

# Unquoted tokens that mean SQL NULL
_NULL_TOKENS = {"NULL", "null", "\\N"}

# Zero/empty datetime markers
_EMPTY_DATETIMES = {"0000-00-00 00:00:00", "", None}


def _iter_statements(content):
    """
    Yield the *body* of every `INSERT INTO rate_agreement ... VALUES ...;`
    statement, correctly skipping ';' inside string literals.

    This is a small state machine so it works even when the value contains
    ';' or ');' inside a string.
    """
    # Match the start of any INSERT for our table, allowing backticks.
    start_re = re.compile(
        r"INSERT\s+INTO\s+`?rate_agreement`?\s*(?:\([^)]*\))?\s*VALUES\s*",
        re.I | re.S,
    )

    pos = 0
    n = len(content)
    while True:
        m = start_re.search(content, pos)
        if not m:
            return

        i = m.end()
        in_str = False
        quote = ""
        start = i
        while i < n:
            ch = content[i]
            if in_str:
                if ch == "\\" and quote == "'":
                    # MySQL backslash escape inside a string
                    i += 2
                    continue
                if ch == quote:
                    if i + 1 < n and content[i + 1] == quote:
                        # doubled quote ('' or "") — still inside the string
                        i += 2
                        continue
                    in_str = False
                i += 1
                continue
            if ch in ("'", '"'):
                in_str = True
                quote = ch
                i += 1
                continue
            if ch == ";":
                break
            i += 1

        yield content[start:i]
        pos = i + 1


def _split_fields(row_body):
    """
    Split the body of a single `(...)` row into raw field strings.
    Correctly handles:
      * commas inside '...' or "..." strings
      * backslash escapes (\\' \\" \\\\ \\n etc.)
      * doubled quotes ('')
      * parentheses inside strings (we only track depth OUTSIDE strings)
    Returns a list of strings (each still quoted/escaped as in the dump).
    """
    fields = []
    buf = []
    depth = 0
    in_str = False
    quote = ""
    i = 0
    n = len(row_body)

    while i < n:
        ch = row_body[i]

        if in_str:
            buf.append(ch)
            if ch == "\\" and quote == "'":
                # copy the escaped char verbatim
                if i + 1 < n:
                    buf.append(row_body[i + 1])
                    i += 2
                    continue
            if ch == quote:
                if i + 1 < n and row_body[i + 1] == quote:
                    buf.append(quote)
                    i += 2
                    continue
                in_str = False
            i += 1
            continue

        if ch in ("'", '"'):
            in_str = True
            quote = ch
            buf.append(ch)
        elif ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            if depth == 0:
                fields.append("".join(buf))
                buf = []
                i += 1
                break
            buf.append(ch)
        elif ch == "," and depth == 1:
            fields.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1

    return fields


def _unescape(raw):
    """
    Turn a raw SQL literal into a Python value:
      * NULL (unquoted)          -> None
      * 'abc' with escapes       -> "abc"
      * "abc" (any escapes)      -> "abc"
      * 123                      -> "123"   (caller does int()/float())
    """
    s = raw.strip()
    if s in _NULL_TOKENS:
        return None
    if s == "":
        return ""
    if s[0] == "'" and s[-1] == "'":
        body = s[1:-1]
    elif s[0] == '"' and s[-1] == '"':
        body = s[1:-1]
    else:
        return s

    out = []
    i = 0
    n = len(body)
    while i < n:
        ch = body[i]
        if ch == "\\" and i + 1 < n:
            nxt = body[i + 1]
            out.append(_ESCAPE_MAP.get(nxt, nxt))
            i += 2
            continue
        if ch == "'" and i + 1 < n and body[i + 1] == "'":
            out.append("'")
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def parse_sql_file(file_path):
    """Return a list of lists of *Python* values (strings/None/numbers as str)."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    rows = []
    for body in _iter_statements(content):
        # Each statement is a comma-separated list of `(...)` groups
        i = 0
        n = len(body)
        while i < n:
            while i < n and body[i] in " \t\r\n,":
                i += 1
            if i >= n or body[i] != "(":
                break
            fields = _split_fields(body[i:])
            if fields:
                rows.append([_unescape(f) for f in fields])
            # Advance past this row's closing ')'
            # ( _split_fields consumed up to ')' )
            # Find matching ')' with the same quote rules:
            depth = 0
            in_str = False
            quote = ""
            while i < n:
                ch = body[i]
                if in_str:
                    if ch == "\\" and quote == "'":
                        i += 2
                        continue
                    if ch == quote:
                        if i + 1 < n and body[i + 1] == quote:
                            i += 2
                            continue
                        in_str = False
                    i += 1
                    continue
                if ch in ("'", '"'):
                    in_str = True
                    quote = ch
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
    return rows


# ---------------------------------------------------------------------------
# Row conversion
# ---------------------------------------------------------------------------

def _clean(val):
    if val is None:
        return None
    s = str(val).strip()
    if s in _EMPTY_DATETIMES:
        return None
    return s


def _clean_dt(val):
    return _clean(val)


def _req_dt(val):
    """Required datetime: NULL / zero becomes epoch fallback."""
    cleaned = _clean(val)
    return cleaned if cleaned else datetime(1970, 1, 1)


def convert_row(row):
    """
    Raw columns (0-based):
      0 id                         1 rate_agreementNo
      2 agent_code                 3 agent_name
      4 startDate                  5 endDate
      6 approveDate                7 rate_agreementLine_ID
      8 timeslot                   9 positionName
      10 priority                  11 program
      12 timeBand                  13 rate
      14 adType                    15 episode_no
      16 limit1                    17 type
      18 lineStartDate             19 lineEndDate
    """
    return {
        "rate_agreementNo": int(row[1]),
        "agent_code": _clean(row[2]),
        "agent_name": _clean(row[3]),
        "startDate": _clean_dt(row[4]),
        "endDate": _clean_dt(row[5]),
        "approveDate": _clean_dt(row[6]),
        "rate_agreementLine_ID": int(row[7]),
        "timeslot": _clean(row[8]),
        "positionName": _clean(row[9]),
        "priority": _clean(row[10]),
        "program": _clean(row[11]),
        "timeBand": _clean(row[12]),
        "rate": float(row[13]),
        "adType": _clean(row[14]),
        "episode_no": int(row[15]),
        "limit1": float(row[16]),
        "type": _clean(row[17]),
        "lineStartDate": _req_dt(row[18]),
        "lineEndDate": _req_dt(row[19]),
    }


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_data(sql_path="rate_agreement.sql", skipped_path="skipped_rows.tsv"):
    db: Session = SessionLocal()

    rows = parse_sql_file(sql_path)

    EXPECTED_COLUMNS = 20
    total_rows = len(rows)

    bad_columns = []
    missing_dates = []
    parse_errors = []

    objects = []
    for idx, r in enumerate(rows):
        if len(r) != EXPECTED_COLUMNS:
            bad_columns.append((idx, r))
            continue
        try:
            data = convert_row(r)
        except Exception as e:
            parse_errors.append((idx, r, str(e)))
            continue
        # Only skip if the *source* zero dates are in the row;
        # _req_dt already falls back to epoch, so this only triggers
        # if you change _req_dt to return None.
        if data["lineStartDate"] is None or data["lineEndDate"] is None:
            missing_dates.append((idx, r))
            continue
        objects.append(RateAgreement(**data))

    # Log skipped rows so nothing is silently lost
    with open(skipped_path, "w", encoding="utf-8") as f:
        f.write("reason\trow_index\traw_row\n")
        for idx, r in bad_columns:
            f.write(f"bad_columns\t{idx}\t{r!r}\n")
        for idx, r in missing_dates:
            f.write(f"missing_dates\t{idx}\t{r!r}\n")
        for idx, r, err in parse_errors:
            f.write(f"parse_error:{err}\t{idx}\t{r!r}\n")

    # Write in chunks so one constraint violation doesn't abort everything
    inserted = 0
    db_rejected = 0
    CHUNK = 500
    for start in range(0, len(objects), CHUNK):
        chunk = objects[start:start + CHUNK]
        try:
            db.bulk_save_objects(chunk)
            db.commit()
            inserted += len(chunk)
        except IntegrityError as e:
            db.rollback()
            # Fall back to per-row to isolate the bad row(s)
            for obj in chunk:
                try:
                    db.add(obj)
                    db.commit()
                    inserted += 1
                except Exception as e2:
                    db.rollback()
                    db_rejected += 1
                    print(
                        f"❌ DB rejected row "
                        f"rate_agreementNo={getattr(obj, 'rate_agreementNo', '?')}, "
                        f"line_ID={getattr(obj, 'rate_agreementLine_ID', '?')}: "
                        f"{getattr(e2, 'orig', e2)}"
                    )

    db.close()

    total_skipped = len(bad_columns) + len(missing_dates) + len(parse_errors)

    print("\n" + "=" * 55)
    print(f"📊 Total rows parsed       : {total_rows}")
    print(f"✅ Inserted                : {inserted}")
    print(f"❌ Rejected by DB          : {db_rejected}")
    print(f"❌ Skipped before DB       : {total_skipped}")
    print(f"   ├─ Bad column count     : {len(bad_columns)}")
    print(f"   ├─ Missing dates        : {len(missing_dates)}")
    print(f"   └─ Parse errors         : {len(parse_errors)}")
    print(f"📝 Skipped rows written to : {os.path.abspath(skipped_path)}")
    print("=" * 55)


if __name__ == "__main__":
    load_data()