"""
Fix unparsed collects: re-parse collects fields that failed due to semicolons
or other edge cases, creating artifact_work links where possible.

Run: python fix_unparsed_collects.py
"""

import re
from models import ENGINE, SessionLocal, Artifact, Work, ArtifactWork, DataQualityFlag, _uuid


def parse_collects_field(collects_str: str) -> list[str]:
    """Parse a collects field that may use semicolons or commas as separators.

    Handles patterns like:
      - "Green Lantern: 1001 Emerald Nights; Superman: Last Stand on Krypton"
      - "X-Men: Ronin (#1-5), Marvel Mangaverse: Avengers Assemble (One Shot)"
      - "Hulk The End GN + Hulk Smash (#1-2) + Startling Stories: The Thing #1"
    """
    if not collects_str:
        return []

    # Split on semicolons first (strongest separator)
    if ";" in collects_str:
        parts = [p.strip() for p in collects_str.split(";") if p.strip()]
    # Split on " + " (used as separator in some entries)
    elif " + " in collects_str:
        parts = [p.strip() for p in collects_str.split(" + ") if p.strip()]
    # Fall back to comma split, but only if commas aren't inside parens
    else:
        parts = re.split(r",\s*(?![^()]*\))", collects_str)
        parts = [p.strip() for p in parts if p.strip()]

    return parts


def fix_unparsed():
    db = SessionLocal()
    try:
        flags = (
            db.query(DataQualityFlag)
            .filter(DataQualityFlag.flag_type == "unparsed_collects")
            .all()
        )

        if not flags:
            print("No unparsed_collects flags found.")
            return

        print(f"Found {len(flags)} unparsed_collects flag(s):\n")
        fixed = 0

        for flag in flags:
            artifact = db.query(Artifact).filter(
                Artifact.artifact_id == flag.entity_id
            ).first()
            if not artifact:
                print(f"  SKIP: Artifact {flag.entity_id[:8]}... not found")
                continue

            # Extract the collects string from the description
            match = re.search(r"Could not parse Collects field: (.+)", flag.description)
            if not match:
                print(f"  SKIP: Cannot extract collects from flag description")
                continue

            collects_str = match.group(1)
            titles = parse_collects_field(collects_str)

            print(f"  Artifact: {artifact.title}")
            print(f"  Collects: {collects_str}")
            print(f"  Parsed {len(titles)} title(s): {titles}")

            # Check which works already exist for this artifact
            existing_links = (
                db.query(ArtifactWork)
                .filter(ArtifactWork.artifact_id == artifact.artifact_id)
                .count()
            )

            if existing_links > 0:
                print(f"  Already has {existing_links} work link(s) — skipping\n")
                continue

            for i, title in enumerate(titles):
                # Clean up parenthetical issue numbers for work title
                clean_title = re.sub(r"\s*\(#[^)]+\)\s*$", "", title).strip()
                clean_title = re.sub(r"\s*#\d+[-–]\d+\s*$", "", clean_title).strip()

                if not clean_title:
                    continue

                # Try to find an existing work with this title
                work = db.query(Work).filter(Work.title.ilike(clean_title)).first()
                if not work:
                    work = Work(
                        work_id=_uuid(),
                        title=clean_title,
                        work_type="Comic",
                    )
                    db.add(work)
                    db.flush()
                    print(f"    Created Work: {clean_title}")
                else:
                    print(f"    Found existing Work: {work.title}")

                link = ArtifactWork(
                    id=_uuid(),
                    artifact_id=artifact.artifact_id,
                    work_id=work.work_id,
                    position=i + 1,
                    is_partial=False,
                    collects_note=title,
                )
                db.add(link)

            fixed += 1
            print()

        if fixed > 0:
            confirm = input(f"Commit {fixed} fix(es)? [y/N] ")
            if confirm.lower() == "y":
                db.commit()
                print(f"Done. {fixed} artifact(s) re-parsed and linked.")
            else:
                db.rollback()
                print("Aborted.")
        else:
            print("No artifacts needed fixing.")
    finally:
        db.close()


if __name__ == "__main__":
    fix_unparsed()
