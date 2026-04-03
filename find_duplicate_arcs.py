"""Find duplicate story arcs by name (case-insensitive).

Read-only script — does not modify the database.
"""

from sqlalchemy import func
from database import SessionLocal
from models import StoryArc, WorkArcMembership

db = SessionLocal()

# Group arcs by lowercased name, find duplicates
dupes = (
    db.query(func.lower(StoryArc.name).label("lname"), func.count().label("cnt"))
    .filter(StoryArc.deleted_at.is_(None))
    .group_by(func.lower(StoryArc.name))
    .having(func.count() > 1)
    .all()
)

if not dupes:
    print("No duplicate arcs found.")
else:
    print(f"Found {len(dupes)} duplicate arc name(s):\n")
    for row in dupes:
        arcs = (
            db.query(StoryArc)
            .filter(func.lower(StoryArc.name) == row.lname, StoryArc.deleted_at.is_(None))
            .all()
        )
        print(f'  "{arcs[0].name}" — {len(arcs)} copies:')
        for arc in arcs:
            work_count = (
                db.query(WorkArcMembership)
                .filter(WorkArcMembership.arc_id == arc.arc_id)
                .count()
            )
            print(f"    ID {arc.arc_id}  |  {work_count} work(s)")
        print()

db.close()
