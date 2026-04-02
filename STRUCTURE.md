# Repository Structure

> **Maintainers:** Any time files are added, moved, or removed, update this document to reflect the change. Include a one-line description for each new file.

```
Library-Management/
├── Utskomia_PRD_1.1.md        # Product Requirements Document (living spec, authoritative)
├── models.py                   # SQLAlchemy ORM models for all 15 tables
├── utskomia.db                 # Live SQLite database (~1,062 artifacts, ~1,457 works)
├── Our Library-3.xlsx          # Original source spreadsheet (reference / re-migration)
├── sample_data.json            # Sample data export for UI prototyping (34 artifacts, 48 works)
├── CHANGELOG.md                # Versioned change log
├── DECISIONS.md                # Implementation decisions log (supplements PRD Section 13)
├── STRUCTURE.md                # This file — repo layout and descriptions
├── .gitignore                  # Git ignore rules
│
└── Archive/                    # One-time scripts and superseded documents
    ├── Utskomia_PRD.md         # PRD v1.0 (superseded by v1.1)
    ├── migrate.py              # One-shot xlsx→SQLite migration script
    ├── verify.py               # Migration-time self-verification (30 checks)
    ├── validate_migration.py   # Red Teamer validation script (6 layers)
    ├── validation_report.json  # Red Teamer output (PASS_WITH_WARNINGS → fixed)
    ├── migration_report.json   # Migration script output (entity counts, parse stats)
    ├── apply_fixes.py          # Post-validation fixes (Collects parsing, creator merges)
    └── patch_completion_status.py  # D-028 schema patch (completion_status → story_arcs)
```

## Conventions

- **Active files** live in the repo root. These are inputs to the next phase of work.
- **Archive/** holds completed one-time scripts, superseded docs, and historical snapshots. Files here should not be modified — they exist for reference only.
- **Backup .db files** are gitignored. Create them locally before destructive operations.
- **`.claude/`** (Claude Code settings) is gitignored.
