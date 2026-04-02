# Changelog

## [0.7.0] - 2026-04-03

### Added (Frontend — Phase 1E Complete)
- Full React + TypeScript + Tailwind frontend with Stitch design system
- Vite dev server with API proxy to FastAPI backend
- CORS middleware on FastAPI backend for development
- App Shell: Glassmorphism TopNav, sidebar with format categories, React Router v6
- Profile system: Netflix-style selector with localStorage persistence
- 12 pages: MyLibrary browse (grid/list), Artifact Detail (inline edit, danger zone), Work Detail (series/arc nav, prev/next), Story Arc Timeline (completion bar, MISSING placeholders), Comics/Novels/NonFiction/Magazines browse, Add to Library form, Search Results, Review Queue, Collection Detail, Creator Detail
- TanStack Query for all data fetching with mutations and cache invalidation
- TypeScript types matching all backend Pydantic schemas
- Cover images via `/api/artifacts/{id}/cover` endpoint (JPEG or SVG placeholder)
- Responsive: desktop sidebar, tablet/mobile hamburger menu
- Cross-browser: Safari, Firefox, Chrome (desktop + mobile)

## [0.6.0] - 2026-04-03

### Added (Frontend — Page Components, Batch 2)
- `StoryArcTimeline.tsx`: Arc detail with hero, completion counter, progress bar, expandable sub-arcs, ordered works list with missing-position placeholders
- `ComicsBrowse.tsx`: Three-tab comics hub (Arcs tree, Graphic Novels grid, Comic Issues grid) with lazy tab loading
- `NovelsBrowse.tsx`: Novels grid aggregating Hardcover, Paperback, Kindle, Audible formats
- `NonFictionBrowse.tsx`: Non-fiction artifacts grid with same browse pattern
- `MagazinesBrowse.tsx`: Magazines grid filtered by Magazine format
- `AddToLibrary.tsx`: New artifact creation form with collapsible sections (Publisher & Year, Physical Details, Ownership, Identifiers, Notes), debounced submit, React Query mutation
- `SearchResults.tsx`: Global search results grouped by entity type (Creators, Arcs, Artifacts, Works, Collections) with badges and empty state
- `ProfileSelector.tsx`: Netflix-style profile picker for Utsav, Utkarsh, Som with colored avatars
- `ReviewQueue.tsx`: Data quality flags list with resolve/dismiss mutations, flag type badges, entity links
- `CollectionDetail.tsx`: Collection detail with progress bar, ordered works list, sub-collection cards
- `CreatorDetail.tsx`: Creator detail with works grouped by role using formatRoleLabel utility
- `NotFound.tsx`: 404 page with Material icon and home link

## [0.5.0] - 2026-04-03

### Added (Frontend — Page Components)
- `MyLibrary.tsx`: Main browse page with grid/list toggle (localStorage-persisted), search, format filter from URL params, sort dropdown (Title A-Z, Date Added, Edition Year), skeleton loading, empty state, pagination
- `ArtifactDetail.tsx`: Full artifact detail page with blurred cover hero, metadata bento grid (location, condition, size, owner), inline editing mode (title, format, publisher, size, notes), reprint lineage, ordered contents list, copies with lending info, collapsible danger zone (pirated flag toggle, delete with confirmation), React Query mutations
- `WorkDetail.tsx`: Work detail page with creators grouped by role, series position with prev/next navigation (fetches collection), arc position with prev/next (fetches arc), volume run display, "In Your Library" cross-reference list, external links (Goodreads, ComicVine), subject tags, reading status via useProfile hook

## [0.4.0] - 2026-04-03

### Added
- `cover_image_path` column on `artifacts` table to store cover image file paths
- `GET /api/artifacts/{id}/cover` endpoint: returns the actual cover image (JPEG) or a generated SVG placeholder for items without covers
- Static file serving at `/covers/` for direct cover image access
- One-time backfill script (`Archive/backfill_covers.py`) to populate cover paths from `cover_manifest.csv`

### Changed
- `ArtifactSummary`, `ArtifactDetail`, `ArtifactCreate`, `ArtifactUpdate` schemas now include `cover_image_path`
- `database.py` migration adds `cover_image_path` column idempotently at startup

## [0.3.0] - 2026-04-02

### Added (FastAPI Backend — PRD Section 8)
- FastAPI application (`main.py`) with 9 router modules and 32 API endpoints
- Full CRUD for: Artifacts, Works, Collections, Story Arcs, Creators
- Activity Ledger with automatic `reading_status` cache table updates
- Lending workflow: `PUT /copies/{id}/lend` and `PUT /copies/{id}/return`
- Data quality flag endpoints: list (filterable) and resolve/dismiss
- Global search endpoint across all entity types (`GET /api/search?q=`)
- Creator merge/deduplication endpoint (`POST /api/creators/merge`)
- Tree view support for Collections and Story Arcs (`?tree=true`)
- Pydantic request/response schemas (`schemas/` directory)
- Service modules for reading status logic and creator merge (`services/`)
- Soft delete via `deleted_at` column on `artifacts` and `works` tables
- Test suite: 54 tests covering all critical paths (dual-story artifacts, cross-volume arcs, creator merge, lending flow, reading status cache)

### Changed
- Added `deleted_at` column to `Work` and `Artifact` models for soft deletes
- Database migration runs at app startup (idempotent `ALTER TABLE`)

## [0.2.0] - 2026-04-02

### Changed (D-028: completion_status schema fix)
- Added `completion_status` column to `story_arcs` table (Complete/Incomplete)
- Re-derived per-arc completion from xlsx: 122 arcs matched (40 Complete, 82 Incomplete, 5 NULL)
- Cleared `volume_runs.completion_status` for all non-Serialized runs (273 cleared)
- Kept `Not Pursuing` only on 8 Serialized volume_runs
- Updated SQLAlchemy model (`StoryArc.completion_status`, `VolumeRun.completion_status` comments)
- 4 arc names unmatched due to parsing differences (Deadbolt, The Tomb, The Chain, Ultimate Six/Nightmare) — deferred to manual fix

## [0.1.1] - 2026-04-02

### Fixed (Red Teamer post-validation fixes)
- Parsed 11 previously-unparsed Collects entries into 34 new Works
- Split DC Elseworlds artifact into 2 Works with correct per-work creator roles
- Merged 4 duplicate creators (Gregg/Greg Rucka, Mike W/Mike W. Barr, Min S/Min S. Ku, Issac/Isaac Asimov)
- Dismissed 143 flags (80 name false positives, 36 missing ISBNs, 24 conflicting data, 1 Calvin & Hobbes collects, 2 remaining name flags for merged creators)
- Resolved 13 flags (4 creator merges + 9 collects parses)

### Known Issues (deferred)
- completion_status stored on volume_runs but should be on story_arcs (PRD schema fix needed — see D-028)
- New X-Men Super Special: Work title contains raw Collects text as name (complex multi-series, correctly not auto-parsed, but title needs manual cleanup)

## [0.1.0] - 2026-04-02

### Added
- SQLAlchemy 2.0 ORM models for 15 tables (`models.py`)
- Migration script reading `Our Library-3.xlsx` and populating `utskomia.db` (`migrate.py`)
- Independent verification script (`verify.py`) — 30/30 checks passed
- Populated SQLite database (`utskomia.db`): 1,062 artifacts, 1,423 works, 650 creators
- Migration report (`migration_report.json`)
- Sample data export (`sample_data.json`): 34 artifacts, 48 works, 10 creators
- Implementation decisions log (`DECISIONS.md`)

### Migration coverage
- Novels: 269 artifacts
- Hindi Books: 5 artifacts
- Non-fiction: 84 artifacts
- Magazines: 18 artifacts
- Comics (GNs): 96 artifacts, 385 works (from Collects parsing: 50 parsed, 12 flagged, 27 skipped)
- Comics (Issues): 590 artifacts, 673 works (83 dual-story issues)
- 127 story arcs, 328 arc memberships
- 55 activity ledger entries, 55 reading status records
- 156 data quality flags (36 missing ISBN, 84 name inconsistency, 12 unparsed collects, 24 conflicting data)
