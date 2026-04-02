# Changelog

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
