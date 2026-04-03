"""Fix known data typos in works, artifacts, and story arcs.

Run with: python fix_typos.py [--dry-run]
"""

import sys
from database import SessionLocal
from models import Work, Artifact, StoryArc

TYPO_MAP = {
    "Bood Debt": "Blood Debt",
}

dry_run = "--dry-run" in sys.argv

db = SessionLocal()
fixed = 0

for wrong, correct in TYPO_MAP.items():
    for Model, field, label in [
        (Work, "title", "Work"),
        (Artifact, "title", "Artifact"),
        (StoryArc, "name", "StoryArc"),
    ]:
        col = getattr(Model, field)
        rows = db.query(Model).filter(col.ilike(f"%{wrong}%")).all()
        for row in rows:
            old_val = getattr(row, field)
            new_val = old_val.replace(wrong, correct)
            if old_val != new_val:
                print(f"  {label} [{getattr(row, Model.__table__.primary_key.columns.keys()[0])}]: "
                      f'"{old_val}" → "{new_val}"')
                if not dry_run:
                    setattr(row, field, new_val)
                fixed += 1

if fixed:
    if dry_run:
        print(f"\n{fixed} fix(es) found. Run without --dry-run to apply.")
    else:
        db.commit()
        print(f"\n{fixed} fix(es) applied.")
else:
    print("No typos found.")

db.close()
