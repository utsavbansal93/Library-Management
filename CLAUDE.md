# Utskomia Library — Agent Instructions

## File Structure Maintenance
When adding, moving, or removing files in this repo, **always update `STRUCTURE.md`** with the new file path and a one-line description. This keeps the repo navigable for all agents and future contributors.

## Key References
- **PRD:** `Utskomia_PRD_1.1.md` is the authoritative spec. Read it before starting work.
- **Decisions:** Check `DECISIONS.md` for implementation choices not in the PRD.
- **Schema:** `models.py` has the SQLAlchemy models. The DB is `utskomia.db`.
- **Changelog:** Log all changes in `CHANGELOG.md` with date and version.
