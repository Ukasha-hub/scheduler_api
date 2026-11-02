"""
make_all_nullable.py

Generate (and optionally apply) the ALTER TABLE statements needed to make
every column of `rate_agreement` nullable, except:
  - primary key columns (Postgres forbids nullable PKs)
  - anything listed in EXCLUDE

Run in dry-run mode first:
    python make_all_nullable.py

Then apply:
    python make_all_nullable.py --apply

Uses the same SQLAlchemy engine/session your app already uses, so it works
against whatever DB `app.db.session` points at.
"""

import sys
import argparse

from sqlalchemy import inspect, text

from app.db.base import Base          # noqa: F401  (ensures models are imported)
from app.db.session import engine
from app.models.rate_agreement import RateAgreement


TABLE = RateAgreement.__tablename__

# Never touch these even if you "make everything nullable"
ALWAYS_EXCLUDE = {"id"}   # PK


def build_statements(exclude=None, only=None):
    """
    Return the list of `ALTER TABLE ... ALTER COLUMN ... DROP NOT NULL;`
    statements needed to make every (eligible) column nullable.

    exclude : set of column names to *never* alter
    only    : optional set of column names to restrict to (overrides exclude
              for those columns; use to target a subset)
    """
    exclude = set(exclude or ()) | ALWAYS_EXCLUDE

    insp = inspect(engine)
    existing_cols = {c["name"]: c for c in insp.get_columns(TABLE)}

    model_cols = list(RateAgreement.__table__.columns)
    statements = []

    for col in model_cols:
        name = col.name
        if name in exclude:
            continue
        if only is not None and name not in only:
            continue

        db_col = existing_cols.get(name)
        if db_col is None:
            print(f"⚠️  Column `{name}` exists in model but not in DB — skipping")
            continue
        if db_col.get("nullable", True):
            continue  # already nullable

        statements.append(
            f'ALTER TABLE "{TABLE}" ALTER COLUMN "{name}" DROP NOT NULL;'
        )

    return statements


def apply(statements, engine=engine):
    if not statements:
        print("✅ Nothing to do — all eligible columns are already nullable.")
        return
    with engine.begin() as conn:
        for stmt in statements:
            print(f"▶ {stmt}")
            conn.execute(text(stmt))
    print(f"\n✅ Applied {len(statements)} ALTER statement(s).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--apply", action="store_true",
        help="Actually execute the ALTER statements (default: dry-run)."
    )
    ap.add_argument(
        "--exclude", nargs="*", default=[],
        help="Column names to keep NOT NULL (space-separated). `id` is always excluded.",
    )
    ap.add_argument(
        "--only", nargs="*", default=None,
        help="Only touch these columns (overrides --exclude for them).",
    )
    args = ap.parse_args()

    stmts = build_statements(
        exclude=set(args.exclude),
        only=set(args.only) if args.only else None,
    )

    print(f"📋 Table: {TABLE}")
    print(f"📋 Statements to run: {len(stmts)}")
    for s in stmts:
        print("   ", s)

    if args.apply:
        print()
        apply(stmts)
    else:
        print(
            "\nℹ️  Dry-run only. Re-run with --apply to execute.\n"
            "   Example: python make_all_nullable.py --apply "
            "--exclude rate_agreementNo rate_agreementLine_ID"
        )


if __name__ == "__main__":
    sys.exit(main())