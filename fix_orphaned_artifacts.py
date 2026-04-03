"""
Fix orphaned artifacts: find artifacts with no linked Works in artifact_works
and create appropriate Work records + links for them.

Run: python fix_orphaned_artifacts.py
"""

import sys
from models import ENGINE, SessionLocal, Artifact, Work, ArtifactWork, _uuid


FORMAT_TO_WORK_TYPE = {
    "Comic Issue": "Comic",
    "Graphic Novel": "Comic",
    "Hardcover": "Novel",
    "Paperback": "Novel",
    "Kindle": "Novel",
    "Audible": "Novel",
    "Magazine": "Magazine",
}


def fix_orphans():
    db = SessionLocal()
    try:
        orphans = (
            db.query(Artifact)
            .outerjoin(ArtifactWork, Artifact.artifact_id == ArtifactWork.artifact_id)
            .filter(ArtifactWork.id.is_(None), Artifact.deleted_at.is_(None))
            .all()
        )

        if not orphans:
            print("No orphaned artifacts found.")
            return

        print(f"Found {len(orphans)} orphaned artifact(s):\n")
        for a in orphans:
            print(f"  - [{a.format}] {a.title} ({a.artifact_id[:8]}...)")

        confirm = input("\nCreate Work records and link them? [y/N] ")
        if confirm.lower() != "y":
            print("Aborted.")
            return

        for a in orphans:
            work_type = FORMAT_TO_WORK_TYPE.get(a.format, "Comic")
            work = Work(
                work_id=_uuid(),
                title=a.title,
                work_type=work_type,
            )
            db.add(work)
            db.flush()

            link = ArtifactWork(
                id=_uuid(),
                artifact_id=a.artifact_id,
                work_id=work.work_id,
                position=1,
                is_partial=False,
            )
            db.add(link)
            print(f"  Created Work ({work_type}) for: {a.title}")

        db.commit()
        print(f"\nDone. {len(orphans)} orphan(s) fixed.")
    finally:
        db.close()


if __name__ == "__main__":
    fix_orphans()
