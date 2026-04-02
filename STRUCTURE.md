# Repository Structure

> **Maintainers:** Any time files are added, moved, or removed, update this document to reflect the change. Include a one-line description for each new file.

```
Library-Management/
├── Utskomia_PRD_1.1.md        # Product Requirements Document (living spec, authoritative)
├── models.py                   # SQLAlchemy ORM models for all 16 tables
├── main.py                     # FastAPI application entry point (uvicorn main:app)
├── database.py                 # DB session dependency (get_db) and startup migrations
├── utskomia.db                 # Live SQLite database (~1,062 artifacts, ~1,457 works)
├── Our Library-3.xlsx          # Original source spreadsheet (reference / re-migration)
├── sample_data.json            # Sample data export for UI prototyping (34 artifacts, 48 works)
├── CHANGELOG.md                # Versioned change log
├── DECISIONS.md                # Implementation decisions log (supplements PRD Section 13)
├── STRUCTURE.md                # This file — repo layout and descriptions
├── .gitignore                  # Git ignore rules
├── .env                        # Local secrets (gitignored) — COMICVINE_API_KEY
│
├── cover_images/               # Scraped cover images (671+ files, ~30 MB)
│   └── *.jpg                   # Named by convention: novel_{ISBN}.jpg, issue_{vol}_{num}.jpg, etc.
├── cover_manifest.csv          # Per-item scrape log: filename, source, status, error_detail
│
├── schemas/                    # Pydantic request/response models
│   ├── __init__.py
│   ├── common.py               # Shared brief schemas, OrmBase, pagination helpers
│   ├── artifacts.py            # Artifact + Copy schemas
│   ├── works.py                # Work schemas
│   ├── collections.py          # Collection schemas (with tree view)
│   ├── arcs.py                 # StoryArc schemas (with tree view)
│   ├── creators.py             # Creator schemas (with merge request/response)
│   ├── activity.py             # ActivityLedger + ReadingStatus schemas
│   ├── flags.py                # DataQualityFlag schemas
│   └── search.py               # Global search response schema
│
├── routers/                    # FastAPI route handlers (one file per domain)
│   ├── __init__.py
│   ├── artifacts.py            # Artifact CRUD + copy creation (6 endpoints)
│   ├── works.py                # Work CRUD (5 endpoints)
│   ├── collections.py          # Collection CRUD + tree view (4 endpoints)
│   ├── arcs.py                 # StoryArc CRUD + tree view + cross-volume order (4 endpoints)
│   ├── creators.py             # Creator CRUD + merge/dedup (5 endpoints)
│   ├── activity.py             # Activity logging + reading status cache (2 endpoints)
│   ├── copies.py               # Copy update + lending workflow (3 endpoints)
│   ├── flags.py                # Data quality flag list + resolve/dismiss (2 endpoints)
│   └── search.py               # Global search across all entities (1 endpoint)
│
├── services/                   # Business logic modules
│   ├── __init__.py
│   ├── activity.py             # Reading status cache upsert logic
│   └── creators.py             # Creator merge/deduplication logic
│
├── tests/                      # pytest test suite (54 tests)
│   ├── __init__.py
│   ├── conftest.py             # In-memory SQLite, TestClient, seed data fixtures
│   ├── test_artifacts.py       # Artifact CRUD + dual-story retrieval tests
│   ├── test_works.py           # Work CRUD + soft delete tests
│   ├── test_collections.py     # Collection CRUD + tree view tests
│   ├── test_arcs.py            # Arc CRUD + cross-volume navigation tests
│   ├── test_creators.py        # Creator CRUD + merge/dedup tests
│   ├── test_activity.py        # Activity logging + reading status cache tests
│   ├── test_copies.py          # Copy update + lending flow tests
│   ├── test_flags.py           # Data quality flag tests
│   └── test_search.py          # Global search tests
│
├── frontend/                   # React (Vite + TypeScript + Tailwind) SPA
│   └── src/
│       ├── api/                # API client wrappers (one per domain)
│       ├── components/         # Reusable UI components
│       ├── hooks/              # Custom React hooks (useProfile, etc.)
│       ├── lib/                # Utility functions (cn, coverUrl, etc.)
│       ├── types/              # TypeScript interfaces matching backend schemas
│       └── pages/              # Page-level route components
│           ├── MyLibrary.tsx   # Main browse page — grid/list view, search, filter, sort
│           ├── ArtifactDetail.tsx  # Full artifact detail with inline editing & danger zone
│           ├── WorkDetail.tsx  # Work detail with series/arc navigation & cross-references
│           ├── StoryArcTimeline.tsx  # Arc detail with reading order, progress bar, sub-arcs
│           ├── ComicsBrowse.tsx     # Comics hub: Arcs tree, Graphic Novels grid, Issues grid
│           ├── NovelsBrowse.tsx     # Novels grid (Hardcover, Paperback, Kindle, Audible)
│           ├── NonFictionBrowse.tsx # Non-fiction artifacts grid
│           ├── MagazinesBrowse.tsx  # Magazines grid filtered by format
│           ├── AddToLibrary.tsx     # New artifact form with collapsible sections
│           ├── SearchResults.tsx    # Global search results grouped by entity type
│           ├── ProfileSelector.tsx  # Netflix-style profile picker (Utsav, Utkarsh, Som)
│           ├── ReviewQueue.tsx      # Data quality flags list with resolve/dismiss actions
│           ├── CollectionDetail.tsx # Collection detail with works list and sub-collections
│           ├── CreatorDetail.tsx    # Creator detail with works grouped by role
│           └── NotFound.tsx         # 404 page with link back to home
│
└── Archive/                    # One-time scripts and superseded documents
    ├── Utskomia_PRD.md         # PRD v1.0 (superseded by v1.1)
    ├── migrate.py              # One-shot xlsx→SQLite migration script
    ├── verify.py               # Migration-time self-verification (30 checks)
    ├── validate_migration.py   # Red Teamer validation script (6 layers)
    ├── validation_report.json  # Red Teamer output (PASS_WITH_WARNINGS → fixed)
    ├── migration_report.json   # Migration script output (entity counts, parse stats)
    ├── apply_fixes.py          # Post-validation fixes (Collects parsing, creator merges)
    ├── patch_completion_status.py  # D-028 schema patch (completion_status → story_arcs)
    └── backfill_covers.py      # One-time backfill of cover_image_path from cover_manifest.csv
```

## Conventions

- **Active files** live in the repo root. These are inputs to the next phase of work.
- **Archive/** holds completed one-time scripts, superseded docs, and historical snapshots. Files here should not be modified — they exist for reference only.
- **Backup .db files** are gitignored. Create them locally before destructive operations.
- **`.claude/`** (Claude Code settings) is gitignored.
