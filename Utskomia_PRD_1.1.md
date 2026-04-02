# Alexandria Core — Product Requirements Document (PRD)

**Version:** 1.1  
**Last Updated:** 2026-04-02  
**Status:** Approved for Phase 1 Implementation  
**Owner:** Utsav (Product Owner)  
**Source Data:** `Our_Library-3.xlsx` (uploaded in this project)

### Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-02 | Initial PRD covering schema, migration, UI, scraping workflow, red teamer spec |
| 1.0.1 | 2026-04-02 | Post-review additions: `internal_sku` on Copies, `volume_number` on Volume_Runs, `reading_status` cache table, dual-story migration implementation note, two-step delete confirmation. Decisions D-022 through D-027. |
| 1.1 | 2026-04-02 | **Schema correction:** Moved `completion_status` (Y/N) from `volume_runs` to `story_arcs`. Y/N in the spreadsheet's Complete column is per-story-arc, not per-volume-run. Only S (Serialized/Not Pursuing) stays on volume_runs. Discovered during Red Teamer validation — the v1.0 design caused 24 spurious conflicting_data flags from incorrect majority-vote aggregation. Sections 5.2, 6.3.6 updated. Decision D-028. |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Context & Motivation](#2-context--motivation)
3. [Infrastructure & Tech Stack](#3-infrastructure--tech-stack)
4. [Data Architecture](#4-data-architecture)
5. [Relational Schema](#5-relational-schema)
6. [Migration Specification](#6-migration-specification)
7. [Migration Red Teamer Specification](#7-migration-red-teamer-specification)
8. [API Specification Outline](#8-api-specification-outline)
9. [UI/UX Requirements](#9-uiux-requirements)
10. [Scraping & Enrichment Workflow](#10-scraping--enrichment-workflow)
11. [Phased Build Plan](#11-phased-build-plan)
12. [Sample Data for UI Prototyping](#12-sample-data-for-ui-prototyping)
13. [Decision Log](#13-decision-log)
14. [Notes for AI Agent Developers](#14-notes-for-ai-agent-developers)

---

## 1. Executive Summary

Alexandria Core is a personal library and collections database replacing a multi-tabbed Google Sheet (`Our_Library-3.xlsx`). It is a bespoke relational database with a web interface, serving as the single source of truth for a highly curated personal library owned by two households: "The Bansal Brothers" (Utsav and Utkarsh) and "Somdutta" (Som).

The library contains ~1,064 items across physical novels, non-fiction, Hindi books, magazines, graphic novels, and individual comic issues. A significant portion (~77%) of comic issues are Indian reprints published by Gotham Comics (an Indian publisher that reprinted licensed DC/Marvel content from 1998-2007), which creates a core data modeling challenge: each physical reprint issue may contain one or more stories originally published under different titles, numbers, and publishers.

The system uses an FRBR-inspired architecture separating the abstract narrative (Work) from the owned physical/digital item (Artifact), connected by a many-to-many join table. This enables tracking a single story across multiple physical formats and tracking multiple stories within a single physical item.

---

## 2. Context & Motivation

### 2.1 What the Spreadsheet Contains

| Sheet | Row Count | Description |
|---|---|---|
| Novels, etc.. | ~269 active | Fiction, SFF, drama, mystery, thriller. Sorted by author. Has series, genre/sous-genre, ISBN, Goodreads links, sparse ratings |
| Hindi Books | 5 | Small collection of Hindi-language literature |
| Non-fiction | ~84 active | Non-fiction books with boolean flags for "Story" (narrative non-fiction) and "Coffee Table" (oversized visual book) |
| Magazines | 18 | Periodicals including The Caravan, Harvard Business Review, Indian Literature, and Comic Jump |
| Comics (GNs) | 96 | Graphic novels and trade paperbacks. 34 are reprints. Has "Collects" field mapping to original issues |
| Comics (Issues) | 590 | Individual comic issues. 456 are reprints (mostly Gotham Comics India). Has dual-story tracking, story arcs, original volume mapping |
| Needed | 1 | Placeholder/wishlist (ignore for migration) |
| Analysis | 57 | Summary statistics (ignore for migration — will be rebuilt as app features) |
| Utsav Target 18 | 25 | 2018 reading goal tracker (ignore for migration — will be rebuilt) |
| Gotham Checklist | 43 | Gap-tracking grid for Gotham Comics runs (Phase 3-4 feature, ignore for migration) |
| Sheet Dynamics | 4 | Dropdown value definitions: statuses, shelf types, reprint flags |

### 2.2 Why the Spreadsheet Breaks Down

- **Flat structure cannot represent many-to-many relationships**: A comic issue containing two original stories requires duplicate column sets (Writer 2, Artist 2, etc.). A third story has no place to go.
- **Creator deduplication is impossible**: "Gaiman, Neil" as novelist and "Gaiman, Neil" as comic writer are unrelated text strings.
- **Series and story arcs are just text labels**: No hierarchical navigation (Cosmere → Stormlight Archive), no arc nesting (Knightfall → Knightquest: The Crusade).
- **No activity history**: Ratings are flat columns, not timestamped events. Re-reads, changed ratings, and reading progress are lost.
- **No lending tracking**: "Lent" is just a status value with no record of to whom or when.

### 2.3 What the Owners Love About It

The spreadsheet represents years of careful, deliberate cataloguing. The owners take pride in:
- The *completeness* of metadata capture — every reprint traced to its original
- The *connections* between items — story arcs spanning volumes, series hierarchies
- Being able to see the entire sprawling collection at a glance
- The depth of knowledge encoded in the Notes field (editorial observations, corrections, cross-references)

**The new system must preserve this feeling of pride and comprehensiveness while solving the structural limitations.**

---

## 3. Infrastructure & Tech Stack

### 3.1 Backend
- **Language:** Python 3.12+
- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.0+
- **Database:** SQLite (single file, portable)
- **Rationale:** Most readable across LLMs (Claude, GPT, Gemini). Python is familiar to the owner (Java/C++ background). FastAPI type hints make the codebase self-documenting. SQLite is appropriate for ~1,000 items and scales to tens of thousands without issue.

### 3.2 Frontend
- **Framework:** React + TypeScript
- **Styling:** Tailwind CSS + shadcn/ui
- **Design Exploration:** Google Stitch (Antigravity) for initial UI prototyping, with Claude Code implementing the production version
- **Performance (Phase 2+):** Consider Pretext.js for fluid text layout in dense browsing views with mixed image/text cards
- **Responsive:** Must work on desktop browser and mobile web (phone)

### 3.3 Hosting
- **Phase 1:** Local development on Mac (localhost)
- **Later:** Cloudflare Tunnel for remote access, eventual containerized deployment to Render

### 3.4 AI Tooling Division of Labor

| Tool | Role |
|---|---|
| **Claude Max (this project chat)** | Architecture, PRD, schema design, decision-making, review |
| **Claude Code** | Implementation — migration scripts, FastAPI backend, React frontend, test cases |
| **Google Stitch (Antigravity)** | UI design exploration and component prototyping with sample data |
| **Red Teamer Agent (Claude Code/Antigravity)** | Migration validation (see Section 7) |

---

## 4. Data Architecture

### 4.1 FRBR-Inspired Two-Level Model

The system separates **Works** (abstract narratives/stories) from **Artifacts** (physical or digital items you own). This is inspired by FRBR (Functional Requirements for Bibliographic Records) but simplified from four levels (Work → Expression → Manifestation → Item) to two (Work → Artifact) with an additional Copies table for rare cases of duplicate physical items.

Key relationships:
- One Work can appear in many Artifacts (Batman #455 story exists in both your Gotham reprint and your Knightfall TPB)
- One Artifact can contain many Works (Gotham Amazing Spider-Man #3 contains ASM #34 and #35)
- Works belong to Collections (series) and Story Arcs
- Artifacts have Copies (usually 1, rarely 2)
- Creators link to Works (author, writer, artist) or Artifacts (translator, narrator/performer)

### 4.2 Navigation Mental Model

The app presents three perspectives on the same data:

| Perspective | Entry Point | What User Sees | Underlying Entity |
|---|---|---|---|
| **My Library** | "What do I own?" | Physical/digital items on shelves. Cover images, format badges, location info | Artifacts + Copies |
| **Stories & Series** | "What narratives exist?" | Works organized by series, arcs, timelines. Reading orders. | Works, Collections, Story Arcs |
| **People** (Phase 2) | "Who created what?" | Creator pages with works grouped by role | Creators, Creator_Roles |

Cross-linking is pervasive: from any Artifact you can reach its Works, from any Work you can see which Artifacts contain it.

### 4.3 The Reprint Chain

For Indian reprints, the data model captures:

```
Artifact (what you hold):
  "Batman #7" published by Gotham Comics (Indian reprint, Small size)
    └── contains Work: "Batman #455 — Identity Crisis Part 1"
         ├── Original Volume Run: Batman Vol 1 (DC Comics, 1940-2011)
         ├── Original issue number: 455
         ├── Writer: Alan Grant
         ├── Artist: Norm Breyfogle
         └── Story Arc: Identity Crisis (Part 1 of 2)
```

The Artifact knows its own publisher (Gotham) and the Work knows its original publisher (DC). The Volume Run entity connects them.

---

## 5. Relational Schema

### 5.1 Entity-Relationship Overview

```
Creators ──┐
            ├── Creator_Roles ──┬── Works ──┬── Work_Collections (join)── Collections (self-referencing)
            │                   │           ├── Work_Arc_Membership ──── Story_Arcs (self-referencing)
            │                   │           └── Artifact_Works (join)─── Artifacts ── Copies
            └── Creator_Roles ──┘                                           │
                (some roles link                                            ├── Field_Provenance
                 to Artifacts,                                              └── Data_Quality_Flags
                 e.g. Narrator)
                 
Activity_Ledger ── links to Works (by work_id) and user profiles
Volume_Runs ── represents a specific publishing series (linked from Works)
```

### 5.2 Table Definitions

#### `creators`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| creator_id | UUID | PK | |
| first_name | TEXT | nullable | For cases where only one name is known |
| last_name | TEXT | nullable | |
| display_name | TEXT | NOT NULL | Canonical display: "Neil Gaiman", "Abhijeet Kini" |
| sort_name | TEXT | NOT NULL | For alphabetical sorting: "Gaiman, Neil" |
| aliases | JSON | nullable | Array of strings, e.g. ["Moebius"] for Jean Giraud |
| created_at | DATETIME | NOT NULL | |
| updated_at | DATETIME | NOT NULL | |

#### `creator_roles`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| creator_id | UUID | FK → creators | |
| target_type | TEXT | NOT NULL | Enum: `work`, `artifact` |
| target_id | UUID | NOT NULL | Points to either a work_id or artifact_id |
| role | TEXT | NOT NULL | Enum: `Author`, `Writer`, `Artist`, `Inker`, `Colorist`, `Letterer`, `Editor`, `Translator`, `Narrator/Performer` |
| notes | TEXT | nullable | e.g. "cover artist only" |

**Design note:** `Author` is used for novels/non-fiction. `Writer`/`Artist`/`Inker` etc. are used for comics. `Translator` and `Narrator/Performer` link to Artifacts (they're properties of a specific edition, not the abstract work). All other roles link to Works.

#### `collections`
Self-referencing hierarchy for series, universes, and franchise groupings.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| collection_id | UUID | PK | |
| name | TEXT | NOT NULL | "Discworld", "A Song of Ice and Fire", "The Cosmere" |
| parent_collection_id | UUID | FK → collections, nullable | For nesting: Cosmere → Stormlight Archive |
| collection_type | TEXT | NOT NULL | Enum: `Universe/Franchise`, `Series`, `Sub-series` |
| description | TEXT | nullable | |
| created_at | DATETIME | NOT NULL | |
| updated_at | DATETIME | NOT NULL | |

#### `volume_runs`
Represents a specific comic publishing series with its own numbering.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| volume_run_id | UUID | PK | |
| name | TEXT | NOT NULL | "Batman", "Ultimate Spider-Man", "Doom Patrol" |
| publisher | TEXT | NOT NULL | "DC Comics", "Marvel", "Gotham Comics" |
| start_year | INTEGER | nullable | |
| end_year | INTEGER | nullable | NULL if ongoing |
| volume_qualifier | TEXT | nullable | "Vol 1", "New 52", "(2016)" — free text for disambiguation |
| volume_number | INTEGER | nullable | Integer sequence (1, 2, 3...) for API matching. ComicVine indexes volumes by this number. "Batman Vol 1" → 1, "Batman Vol 2 (New 52)" → 2 |
| narrative_format | TEXT | nullable | Enum: `Arc-based`, `Serialized`, `Anthology`, `Standalone` |
| completion_status | TEXT | nullable | Only valid value: `Not Pursuing` (for Serialized runs). NULL for all other runs. Y/N completion tracking lives on `story_arcs.completion_status`, not here. See D-028. |
| comicvine_url | TEXT | nullable | |
| notes | TEXT | nullable | |
| created_at | DATETIME | NOT NULL | |
| updated_at | DATETIME | NOT NULL | |

**Design note on narrative_format and completion_status:**

`completion_status` on `volume_runs` is ONLY used for Serialized runs (`Not Pursuing`). It should be NULL for all other volume runs. For arc-based completion tracking (Y/N), see `story_arcs.completion_status`.

The original spreadsheet's `Complete` column had these semantics:
- **Y** = "I own all issues in this issue's *story arc*" → stored on `story_arcs.completion_status = Complete`
- **N** = "I'm missing issues from this *story arc*" → stored on `story_arcs.completion_status = Incomplete`
- **S** = Serialized run, not pursuing completion → stored on `volume_runs.narrative_format = Serialized` AND `volume_runs.completion_status = Not Pursuing`

Mixed Y/N values within a single volume run are **correct data** — different issues belong to different arcs with different completion levels. Do NOT aggregate Y/N to the volume_run level.

**PRD v1.0 erratum:** The original PRD incorrectly placed Y/N completion_status on volume_runs and instructed the migration to aggregate by majority vote per volume+publisher. This was corrected in v1.1 after Red Teamer validation discovered 24 spurious conflicting_data flags caused by the incorrect aggregation. See Decision D-028.

#### `works`
The atomic unit of narrative. A single story, novel, issue's worth of content.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| work_id | UUID | PK | |
| title | TEXT | NOT NULL | |
| work_type | TEXT | NOT NULL | Enum: `Novel`, `Non-fiction`, `Hindi Literature`, `Comic Story`, `Magazine Issue`, `Short Story` |
| original_publication_year | INTEGER | nullable | |
| volume_run_id | UUID | FK → volume_runs, nullable | For comic stories: which original run this belongs to |
| issue_number | TEXT | nullable | Original issue number within the volume run. TEXT to handle "Annual 1", "0", etc. |
| subject_tags | JSON | nullable | Array: ["Batman", "Superhero"] or ["Philosophy", "History"]. Replaces flat Subj Category |
| is_narrative_nonfiction | BOOLEAN | nullable | For non-fiction only: does it read as a story? |
| is_coffee_table_book | BOOLEAN | nullable | For non-fiction only: oversized visual format? |
| goodreads_url | TEXT | nullable | |
| comicvine_url | TEXT | nullable | |
| notes | TEXT | nullable | |
| created_at | DATETIME | NOT NULL | |
| updated_at | DATETIME | NOT NULL | |

#### `work_collections` (join table)
Links Works to Collections (series) with ordering.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| work_id | UUID | FK → works | |
| collection_id | UUID | FK → collections | |
| sequence_number | FLOAT | nullable | Supports 1.0, 1.5 (novellas), 0 (prequels), etc. Follows Goodreads publication-order convention |

#### `story_arcs`
Self-referencing hierarchy for story arcs and mega-arcs.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| arc_id | UUID | PK | |
| name | TEXT | NOT NULL | "Knightfall", "Knightquest: The Crusade" |
| parent_arc_id | UUID | FK → story_arcs, nullable | For nesting: Knightfall (mega) → Knightquest: The Crusade |
| total_parts | INTEGER | nullable | From the parenthetical in source data: "Knightfall (19)" → 19 |
| completion_status | TEXT | nullable | Enum: `Complete`, `Incomplete`. Derived from per-issue Y/N values in the spreadsheet's Complete column. See Section 6.3.6 for mapping rules. |
| description | TEXT | nullable | |
| created_at | DATETIME | NOT NULL | |
| updated_at | DATETIME | NOT NULL | |

#### `work_arc_membership` (join table)
Links Works to Story Arcs with positioning.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| work_id | UUID | FK → works | |
| arc_id | UUID | FK → story_arcs | |
| arc_position | INTEGER | nullable | Position within the arc (from Arc # column) |

**Note:** A Work can belong to multiple arcs (e.g., an issue at the intersection of two crossover events).

#### `artifacts`
The physical or digital item you own.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| artifact_id | UUID | PK | |
| title | TEXT | NOT NULL | Display title as printed on the item |
| format | TEXT | NOT NULL | Enum: `Hardcover`, `Paperback`, `Comic Issue`, `Graphic Novel`, `Magazine`, `Kindle`, `Audible` |
| publisher | TEXT | nullable | Publisher of THIS edition (e.g., "Gotham Comics") |
| edition_year | INTEGER | nullable | Year this specific edition was published |
| isbn_or_upc | TEXT | nullable | |
| is_reprint | BOOLEAN | NOT NULL, default FALSE | |
| original_publisher | TEXT | nullable | If reprint: who published the original (e.g., "DC Comics") |
| date_added | DATE | nullable | When added to the library. For migrated items, set to migration date |
| owner | TEXT | NOT NULL, default 'The Bansal Brothers' | Enum: `The Bansal Brothers`, `Somdutta` |
| is_pirated | BOOLEAN | NOT NULL, default FALSE | Suspected pirated/unauthorized copy. UI hides when false |
| issue_number | TEXT | nullable | Issue number within the reprint publisher's series (e.g., "7" for Gotham Batman #7) |
| volume_run_id | UUID | FK → volume_runs, nullable | The reprint's own volume run (if applicable) |
| size | TEXT | nullable | Enum: `Large`, `Small` — for Gotham Comics physical format |
| main_genre | TEXT | nullable | Primary genre (from Novels sheet) |
| sous_genre | TEXT | nullable | Secondary genre (from Novels sheet) |
| goodreads_url | TEXT | nullable | Goodreads link for this specific edition |
| notes | TEXT | nullable | |
| created_at | DATETIME | NOT NULL | |
| updated_at | DATETIME | NOT NULL | |

**Note on genre:** `main_genre` and `sous_genre` are kept on the Artifact for now because they came from the Novel sheet and apply to the edition/book level in the source data. In a future refactor, genre could move to the Work level or become a tagging system. This is logged in the Decision Log.

#### `artifact_works` (join table)
Links Artifacts to Works, with ordering for multi-story issues.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| artifact_id | UUID | FK → artifacts | |
| work_id | UUID | FK → works | |
| position | INTEGER | NOT NULL, default 1 | Story order within the artifact. 1 = first story, 2 = second, etc. |
| is_partial | BOOLEAN | NOT NULL, default FALSE | True if only part of the work is included (see Batman: Gotham Knights #18* case) |
| collects_note | TEXT | nullable | Free text for complex collection descriptions that couldn't be auto-parsed |

#### `copies`
Physical instances of an artifact. Most artifacts have exactly one copy (created automatically during migration).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| copy_id | UUID | PK | |
| artifact_id | UUID | FK → artifacts | |
| copy_number | INTEGER | NOT NULL, default 1 | 1 for first copy, 2 for second, etc. |
| internal_sku | TEXT | nullable | Optional physical identifier (spine label, NFC sticker ID, QR code). For distinguishing identical copies in the real world. Not needed Day 1 but provisioned for future physical tracking. |
| location | TEXT | nullable | Enum: `Large Shelf`, `Small Shelf`, `Box`, `Lent`, `Missing`, `Digital` |
| condition | TEXT | nullable | Free text |
| borrower_name | TEXT | nullable | If location = 'Lent', who has it |
| lent_date | DATE | nullable | If location = 'Lent', when |
| notes | TEXT | nullable | |

#### `activity_ledger`
Infinite event log for all user interactions with Works.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| log_id | UUID | PK | |
| user_profile | TEXT | NOT NULL | Enum: `Utsav`, `Utkarsh`, `Som` |
| work_id | UUID | FK → works | |
| event_type | TEXT | NOT NULL | Enum: `Started_Reading`, `Finished_Reading`, `Rated`, `Reviewed`, `Abandoned/DNF` |
| event_value | TEXT | nullable | Rating as number (e.g., "4.5"), or review text |
| timestamp | DATETIME | NOT NULL | |

**Migration note:** Existing `Uts*` and `Utk*` rating columns become `Rated` events with `timestamp` set to the migration date.

#### `reading_status`
Denormalized cache of each user's current status with each Work. Updated automatically by the API whenever an Activity Ledger event is written. This avoids having to scan the full ledger to determine current state for browse views.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| user_profile | TEXT | NOT NULL | Enum: `Utsav`, `Utkarsh`, `Som` |
| work_id | UUID | FK → works | |
| status | TEXT | NOT NULL, default 'Unread' | Enum: `Unread`, `Reading`, `Finished`, `DNF` |
| current_rating | FLOAT | nullable | Most recent rating value, for quick display |
| last_event_at | DATETIME | nullable | Timestamp of the most recent ledger event |

**Unique constraint:** (`user_profile`, `work_id`) — one row per user per work. Updated (not inserted) when new events arrive. The Activity Ledger remains the source of truth; this table is a convenience cache.

**Migration note:** For migrated ratings, create a `reading_status` row with `status = Finished` (assumption: if you rated it, you read it) and `current_rating` = the rating value.

#### `field_provenance`
Tracks the source of every field value. Lightweight — only populated for scraped or migrated fields.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| entity_type | TEXT | NOT NULL | Table name: `artifacts`, `works`, `creators` |
| entity_id | UUID | NOT NULL | Row ID in that table |
| field_name | TEXT | NOT NULL | Column name |
| source | TEXT | NOT NULL | Enum: `manual`, `migrated`, `scraped:comicvine`, `scraped:openlibrary`, `scraped:goodreads`, `scraped:googlebooks` |
| source_url | TEXT | nullable | URL of the scraped source |
| approved | BOOLEAN | NOT NULL, default FALSE | Has the user reviewed and approved this scraped value? |
| scraped_at | DATETIME | nullable | |

#### `data_quality_flags`
Review queue for migration issues and ongoing data quality.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| flag_id | UUID | PK | |
| entity_type | TEXT | NOT NULL | Table name |
| entity_id | UUID | NOT NULL | Row ID |
| flag_type | TEXT | NOT NULL | Enum: `missing_isbn`, `name_inconsistency`, `unparsed_collects`, `potential_duplicate`, `missing_metadata`, `conflicting_data` |
| description | TEXT | NOT NULL | Human-readable description |
| suggested_fix | TEXT | nullable | What the system thinks should be done |
| status | TEXT | NOT NULL, default 'open' | Enum: `open`, `resolved`, `dismissed` |
| created_at | DATETIME | NOT NULL | |
| resolved_at | DATETIME | nullable | |

---

## 6. Migration Specification

### 6.1 Source File
`Our_Library-3.xlsx` — uploaded in this Claude project.

### 6.2 Sheets to Migrate

| Sheet | Target Entities |
|---|---|
| Novels, etc.. | Works (type=Novel), Artifacts (format=Hardcover/Paperback), Creators, Collections (for Series), Activity_Ledger (for ratings) |
| Hindi Books | Works (type=Hindi Literature), Artifacts, Creators, Activity_Ledger |
| Non-fiction | Works (type=Non-fiction), Artifacts, Creators, Activity_Ledger |
| Magazines | Works (type=Magazine Issue), Artifacts (format=Magazine), Collections (for magazine series) |
| Comics (GNs) | Works (type=Comic Story, potentially many per GN), Artifacts (format=Graphic Novel), Creators, Volume_Runs |
| Comics (Issues) | Works (type=Comic Story), Artifacts (format=Comic Issue), Creators, Volume_Runs, Story_Arcs, Work_Arc_Membership |

**Sheets to IGNORE:** Needed, Analysis, Utsav Target 18, Gotham Checklist, Sheet Dynamics.

### 6.3 Column Mapping Rules

#### 6.3.1 Novels, etc..

| Source Column | Target | Notes |
|---|---|---|
| Title | Work.title AND Artifact.title | Usually identical |
| Author | Creators + Creator_Roles (role=Author) | Split on `;` for multi-author. Parse "Last, First" format into first_name/last_name |
| Translator | Creators + Creator_Roles (role=Translator, target_type=artifact) | |
| Series | Collections (type=Series) | Create Collection if not exists |
| Series no. | work_collections.sequence_number | |
| Year | Work.original_publication_year | Column has leading space: ` Year` |
| Main Genre | Artifact.main_genre | |
| Sous Genre | Artifact.sous_genre | |
| ISBN | Artifact.isbn_or_upc | |
| Goodreads Link | Work.goodreads_url AND/OR Artifact.goodreads_url | |
| Uts* | Activity_Ledger (user=Utsav, event=Rated, value=X, timestamp=migration_date) | Only if non-null |
| Utk* | Activity_Ledger (user=Utkarsh, event=Rated, value=X, timestamp=migration_date) | Only if non-null |
| GR* | **Do not migrate.** This is a Goodreads community average, not user data. Can be re-fetched. |
| Status | Copy.location. "On Shelf" → `Large Shelf` (default). "Lent" → `Lent` |
| Check | **IGNORE** — internal working column |

#### 6.3.2 Hindi Books
Same mapping as Novels, but `work_type = Hindi Literature`. No Translator column. No genre columns. GR* column exists but ignore it (same as Novels).

#### 6.3.3 Non-fiction

| Source Column | Target | Notes |
|---|---|---|
| Title | Work.title, Artifact.title | |
| Author | Creators. Split on `;` | |
| Year | Work.original_publication_year | |
| ISBN | Artifact.isbn_or_upc | |
| Goodreads Link | Work.goodreads_url | |
| Story | Work.is_narrative_nonfiction | "Yes" → true, "No" → false |
| Coffee Table | Work.is_coffee_table_book | "Yes" → true, "No" → false |
| Status | Copy.location | |

#### 6.3.4 Magazines

| Source Column | Target | Notes |
|---|---|---|
| S. no | **Store as Artifact.notes** (reference ID from spreadsheet) | |
| Magazine | Collection.name (type=Series). Also used in Artifact.title construction | |
| Publisher | Artifact.publisher | |
| Volume | Store in Artifact.notes or a magazine-specific metadata field | |
| Number | Artifact.issue_number | |
| Title | Work.title (the cover story title, if present) | Nullable — some magazines have no title |
| Date | Work.original_publication_year (extract year). Artifact.edition_year. Full date in notes | Some dates are NaT (missing). Keep empty. |
| Status | Copy.location | |

**Special note on magazines:** For magazines, the Work and Artifact are effectively 1:1. Each magazine issue is both a Work and an Artifact. The Collection is the magazine series (e.g., "The Caravan", "Comic Jump").

#### 6.3.5 Comics (GNs)

| Source Column | Target | Notes |
|---|---|---|
| Title | Artifact.title | |
| # | Artifact.issue_number (within the GN series, if applicable) | |
| Series Name | Collection (if non-null) | e.g., "Parva Duology" |
| Publisher | Artifact.publisher | |
| Reprint | Artifact.is_reprint | "Yes" → true, "No" → false |
| Original Volume | Volume_Run.name (for the original series) + link | |
| O# | Used to identify the original Work | |
| Original Publisher | Artifact.original_publisher; also Volume_Run.publisher for original run | |
| Original Year | Work.original_publication_year | |
| Writer | Creator (role=Writer, linked to Work) | Split on `;` |
| Artist | Creator (role=Artist, linked to Work) | Split on `;` |
| Collects | **COMPLEX — see Section 6.4** | |
| Link | Artifact.goodreads_url (some are full URLs, some are text descriptions) | |
| ISBN | Artifact.isbn_or_upc | |
| ComicVine Link | Work.comicvine_url or Artifact.notes | |
| Status | Copy.location | |

#### 6.3.6 Comics (Issues) — Most Complex Sheet

| Source Column | Target | Notes |
|---|---|---|
| Volume | Volume_Run (reprint run). Artifact.title derived from Volume + # | |
| # | Artifact.issue_number | |
| Publisher | Artifact.publisher | |
| Subj Category | Work.subject_tags (as JSON array) | |
| Complete | See special handling below | |
| Reprint | Artifact.is_reprint | |
| Original Publisher | Artifact.original_publisher; Volume_Run.publisher (original) | |
| Original Volume | Volume_Run.name (original). Used to identify the Work | |
| O# | Work.issue_number (original) | |
| Story Arc | Story_Arcs.name. Parse parenthetical for total_parts: "Knightfall (19)" → name="Knightfall", total=19 | |
| Arc # | Work_Arc_Membership.arc_position | |
| Writer | Creator (role=Writer, linked to Work) | |
| Artist | Creator (role=Artist, linked to Work) | |
| Link | Work.comicvine_url or goodreads_url depending on content | |
| Original Volume Issue 2 | **Second Work** linked to same Artifact at position=2 | |
| O2# | Second Work's issue_number | |
| Writer 2 | Creator for second Work | |
| Artist 2 | Creator for second Work | |
| Link 2 | Second Work's link | |
| Size | Artifact.size | |
| Status | Copy.location | |
| Utk Rating | Activity_Ledger (user=Utkarsh, event=Rated) | |
| Uts Rating | Activity_Ledger (user=Utsav, event=Rated) | |
| Notes | Artifact.notes | |

**Complete column special handling:**
- `Y` → The story arc this issue belongs to has `story_arcs.completion_status = Complete`
- `N` → The story arc this issue belongs to has `story_arcs.completion_status = Incomplete`
- `S` → `volume_runs.narrative_format = Serialized` AND `volume_runs.completion_status = Not Pursuing`
- For issues with no story arc: Y is implicit (standalone complete story), no completion_status stored anywhere
- When issues in the same arc have conflicting Y/N values, use the majority value for that arc

Note: Y/N applies to the **story arc**, NOT to the volume run. Mixed Y/N within a single volume run is correct data — different issues belong to different arcs with different completion levels. Do NOT aggregate Y/N to the volume_run level. Only `S` applies to the volume_run.

**PRD v1.0 erratum:** This section originally stated "The Complete value applies to the Volume Run" and instructed majority-vote aggregation per volume+publisher. That was incorrect and caused 24 spurious data quality flags during validation. Corrected in v1.1 per Decision D-028.

**Implementation note for dual/multi-story issues:** The database schema supports N works per artifact via the `artifact_works` join table. The current spreadsheet only has columns up to "2" (Writer 2, Artist 2, etc.), but the migration script must NOT hardcode the number "2". Instead, it should dynamically detect any columns matching the pattern `Original Volume Issue N`, `O{N}#`, `Writer N`, `Artist N`, `Link N` and create the corresponding Work records at position N. This ensures the architecture scales if future data entry or imports include three or more stories per issue.

### 6.4 Collects Field Parsing (GNs)

The `Collects` field in the Comics (GNs) sheet contains semi-structured text describing which original issues a graphic novel collects. Examples range from simple to extremely complex:

**Simple (auto-parseable):**
- `"Angry Maushi #1-3"` → 3 Works
- `"Batman: The Dark Knight #1-4"` → 4 Works
- `"Daytripper #1-10"` → 10 Works

**Medium (parseable with care):**
- `"Superman Rebirth #1; Superman v4 (2016) #1-6"` → 7 Works from 2 runs
- `"Daredevil/Spider-Man #1-4 and Daredevil: Ninja #1-3"` → 7 Works from 2 runs

**Complex (flag for manual review):**
- `"New X-Men (#118-120), the Nightcrawler story from X-Men: Unlimited #32, the Blob and Mastermid stories from #33..."` → Multiple runs, partial issue references
- `"Hulk The End GN + Hulk Smash (#1-2) + Startling Stories: The Thing #1"` → Mixed formats

**Special values:**
- `"-"` → No issues collected (standalone work)
- `"DNF"` → Did Not Finish cataloguing. Store as note, do not parse
- `"Everything"` → (Sandman box set) Store as note
- `"All except Tintin in the Congo"` → Store as note

**Migration strategy:**
1. Attempt regex parsing for patterns: `"Title #X-Y"`, `"Title (#X-Y)"`, `"Title Vol N (#X-Y)"`
2. For successfully parsed entries: create Work records and link via Artifact_Works
3. For failed parses: store the raw text in `artifact_works.collects_note` and create a `data_quality_flag` of type `unparsed_collects`
4. Generate a migration report section listing all parse successes and failures for human review

### 6.5 Creator Name Parsing

Source format is "Last, First" (e.g., "Gaiman, Neil"). Multi-creator entries use `;` separator.

**Rules:**
1. Split on `;` first
2. For each name, split on first `,` to get last_name and first_name
3. Set display_name = "First Last" (e.g., "Neil Gaiman")
4. Set sort_name = "Last, First" (e.g., "Gaiman, Neil")
5. Deduplicate: if a creator with matching display_name already exists, reuse them
6. Flag potential near-duplicates for review: "Grant, Alan" vs "Alan Grant", "Fernandes, Luis" appearing across multiple sheets

**Edge cases to handle:**
- "et al" suffixes: "Ballinger, Alexander et al" → create one Creator, note "et al" in notes
- Single names: "Zen", "Various" → set display_name = the name, leave first/last null. "Various" should be a special creator or handled as a note, not a real person.
- Missing creators: some entries have no writer/artist. This is fine — don't create phantom records.

### 6.6 ISBN Handling

The Hindi Books sheet stores ISBNs as floats (e.g., `8.123720e+09`). These must be:
1. Converted to integers first, then to strings
2. Zero-padded to 10 or 13 digits as appropriate (ISBN-10 or ISBN-13)
3. Validated checksum if possible; flag invalid ISBNs

### 6.7 Default Values for New Fields

| Field | Default for migrated items |
|---|---|
| date_added | Migration date (the date the script runs) |
| owner | `The Bansal Brothers` (for all items — source sheet has no ownership column) |
| is_pirated | FALSE |
| copy.location | `Large Shelf` for items with Status "On Shelf" and no Size info. For comics: use Size column to infer shelf. `Large` → `Large Shelf`, `Small` → `Small Shelf` |

---

## 7. Migration Red Teamer Specification

**Purpose:** A separate AI agent (Claude Code or Antigravity instance) validates the migration independently. It should NOT have access to the migration script's code — only to the source xlsx, the output database, and this specification.

### 7.1 Inputs
- Original file: `Our_Library-3.xlsx`
- Migrated database: `alexandria.db` (SQLite)
- Migration report: `migration_report.json` (produced by migration script)
- This PRD (for schema reference)

### 7.2 Validation Layers

**Layer 1: Row Count Verification**
- For each source sheet, count non-empty rows (exclude rows where Title/Volume/Magazine is null)
- Compare against artifact count created from that sheet source
- Report: `{sheet: "Novels, etc..", source_rows: 269, artifacts_created: 269, match: true}`
- Any mismatch is **CRITICAL**

**Layer 2: Field Completeness**
- For every non-null cell in the source xlsx, verify the value exists somewhere in the database
- Use the column mapping rules in Section 6.3 to trace each source column to its DB destination
- Report: percentage of non-null source cells that have a corresponding non-null value in the DB
- Target: 100%. Any loss is flagged with the specific row and field

**Layer 3: Semantic Integrity**
- **Creator deduplication:** Verify that the same person appearing in multiple sheets resolves to one Creator record
- **Multi-author splitting:** For entries with `;` separated authors, verify all Creators exist and are linked
- **Reprint lineage:** For every artifact where `is_reprint = True`, verify original volume and issue number are preserved in the linked Work
- **Dual-story issues:** For the 83 comic issues with `Original Volume Issue 2` populated, verify two Work records exist linked to the artifact at positions 1 and 2
- **Story arc membership:** Verify arc name and position preserved for every source row where Story Arc and Arc # were non-null
- **Series assignment:** Verify novels with Series values are linked to correct Collection with correct sequence_number
- **Complete/S mapping:** Verify S values mapped to `volume_runs.narrative_format=Serialized` and `volume_runs.completion_status=Not Pursuing`. Verify Y/N values mapped to `story_arcs.completion_status` (Complete/Incomplete) on the associated story arc, NOT on volume_runs. Verify volume_runs.completion_status is NULL for non-Serialized runs.

**Layer 4: Edge Case Verification**
Manually verify these specific records known to be tricky:

1. `Batman #22 (Gotham)` — contains Batman #613 AND Batman: Gotham Knights #18* (partial). Verify both Works linked, is_partial=true on the Gotham Knights one
2. `DC Elseworlds: Last Stand on Krypton - Super Special (Gotham)` — original is TWO works: "Green Lantern: 1001 Emerald Nights" AND "Superman: Last Stand on Krypton". Verify both resolved
3. `New X-Men Super Special (Gotham)` — Collects text references 6+ different source series. Verify flagged for manual review, NOT incorrectly auto-parsed
4. `The Incredible Hulk` issue with `Story Arc = "Snake Eyes (2), The Dogs of War (7)"` — dual arc membership. Verify both arcs linked to the Work
5. `Honour Among Thieves/Kane And Abel` (Novel) — compound title, possibly two novels bound together. Verify handling and flag if ambiguous
6. Any novel marked `Status = Lent` — verify Copy.location = `Lent`
7. Hindi books with ISBN stored as float (e.g., `8.123720e+09`) — verify ISBN restored to proper string format like `"8123720009"` or appropriate ISBN
8. `Tulsidas' Ramayana` GN with `Collects = DNF` — verify NOT parsed as an issue range, stored as note
9. `Hulk Special (Gotham)` — original has no Original Volume name (null), but Collects text references 4+ different series. Verify handled correctly
10. `Batman Adventures #28` with note "Only Need to Know is collected, not The Balance" — partial content. Verify is_partial flag or notes preserved

**Layer 5: Referential Integrity**
- Every foreign key reference must resolve to an existing record
- No orphaned rows in any join table
- Every Artifact must have at least one Copy
- Every Artifact must be linked to at least one Work via artifact_works

**Layer 6: Data Quality Flags Audit**
Verify the migration script generated appropriate flags for:
- Artifacts with missing ISBNs (expected: most comics, some novels)
- Creator name format inconsistencies
- GN Collects text that couldn't be auto-parsed
- Potential duplicate Works (same title + year across sheets)
- Empty ratings (should NOT be flagged — sparse ratings are normal)

### 7.3 Output Format

```json
{
  "validation_timestamp": "ISO-8601",
  "overall_status": "PASS | FAIL | PASS_WITH_WARNINGS",
  "source_file_hash": "sha256 of Our_Library-3.xlsx",
  "database_file_hash": "sha256 of alexandria.db",
  "layer_results": {
    "row_counts": {
      "status": "PASS | FAIL",
      "details": [
        {"sheet": "Novels, etc..", "source_rows": 269, "artifacts_created": 269, "match": true}
      ]
    },
    "field_completeness": {
      "status": "PASS | WARN | FAIL",
      "coverage_pct": 99.7,
      "missing_fields": [
        {"sheet": "...", "row": 42, "column": "ISBN", "reason": "not found in DB"}
      ]
    },
    "semantic_integrity": {
      "status": "PASS | FAIL",
      "checks_passed": 6,
      "checks_failed": 0,
      "issues": []
    },
    "edge_cases": {
      "status": "PASS | WARN",
      "results": [
        {"case": "Batman #22 dual-story", "status": "PASS", "details": "..."}
      ]
    },
    "referential_integrity": {
      "status": "PASS | FAIL",
      "orphaned_records": []
    },
    "data_quality_flags": {
      "status": "INFO",
      "total_flags_generated": 47,
      "breakdown": {"missing_isbn": 30, "unparsed_collects": 8, "name_inconsistency": 5, "potential_duplicate": 4}
    }
  }
}
```

---

## 8. API Specification Outline

### 8.1 Core CRUD Endpoints

All endpoints return JSON. Authentication is deferred to Phase 2 (admin password). Profile selection is a simple header or query param: `?profile=Utsav`.

**Artifacts (My Library)**
- `GET /api/artifacts` — List with filtering: format, publisher, location, owner, search query
- `GET /api/artifacts/{id}` — Full detail including linked Works, Copies, Creators, Activity
- `POST /api/artifacts` — Create (minimum required fields: title, format)
- `PUT /api/artifacts/{id}` — Update
- `DELETE /api/artifacts/{id}` — Soft delete (mark inactive, don't destroy)

**Works (Stories)**
- `GET /api/works` — List with filtering: work_type, collection, arc, search
- `GET /api/works/{id}` — Full detail including linked Artifacts, Arcs, Collections, Creators
- `POST /api/works` — Create
- `PUT /api/works/{id}` — Update
- `DELETE /api/works/{id}` — Soft delete

**Collections**
- `GET /api/collections` — List, optionally tree view
- `GET /api/collections/{id}` — Detail with child collections and works
- `POST /api/collections` — Create
- `PUT /api/collections/{id}` — Update

**Story Arcs**
- `GET /api/arcs` — List, optionally tree view
- `GET /api/arcs/{id}` — Detail with works in order, sub-arcs
- `POST /api/arcs` — Create
- `PUT /api/arcs/{id}` — Update

**Creators**
- `GET /api/creators` — List with search
- `GET /api/creators/{id}` — Detail with works grouped by role
- `POST /api/creators` — Create
- `PUT /api/creators/{id}` — Update
- `POST /api/creators/merge` — Merge two creator records (for deduplication)

**Activity Ledger**
- `POST /api/activity` — Log an event (rate, start reading, finish, etc.)
- `GET /api/activity?work_id=X&profile=Utsav` — Activity history for a work

**Copies & Lending**
- `POST /api/artifacts/{id}/copies` — Add a copy
- `PUT /api/copies/{id}` — Update location, condition
- `PUT /api/copies/{id}/lend` — Set location=Lent, record borrower and date
- `PUT /api/copies/{id}/return` — Clear lending info, restore previous location

**Data Quality**
- `GET /api/flags` — List open flags, filterable by type
- `PUT /api/flags/{id}` — Resolve or dismiss a flag

**Search**
- `GET /api/search?q=knightfall` — Global search across all entity types

### 8.2 Required Fields for Creating Items

**Minimum to create an Artifact:** title, format. Everything else is optional.
**Minimum to create a Work:** title, work_type. Everything else is optional.

This ensures the barrier to adding a new book is as low as possible: user types a title, picks a format, and saves. Details can be filled in later manually or via scraping.

---

## 9. UI/UX Requirements

### 9.1 Emotional Brief

This app is a love letter to a hobby. Opening it should feel like walking into a beautiful personal library — pride, warmth, the quiet satisfaction of a well-organized collection.

**It should NOT feel like:**
- A corporate inventory management system
- A bland CRUD admin panel
- An overwhelming wall of data

**It SHOULD feel like:**
- A personal museum of your reading life
- Something you'd show off to a friend who loves books
- Dense with information but never cluttered
- Fast and responsive — things snap into place, transitions are smooth
- Fun to browse even when you're not looking for something specific

### 9.2 Design Principles

1. **Cover-first where possible.** Even with placeholder images, the visual rhythm of book covers in a grid creates the "shelf" feeling. When real covers are added later, the UI should already have space for them.
2. **Information density is a feature, not a bug.** These are power users who love metadata. Don't hide information behind clicks. Show it, but with clear visual hierarchy.
3. **Cross-links are first-class.** Every creator name, series title, arc name, publisher should be clickable and take you somewhere useful.
4. **Edit should be frictionless.** Inline editing where possible. Click a field, change it, done. No separate "edit mode" page.
5. **The pirated flag should be invisible unless true.** When true, show a subtle icon on the detail page only. Never on browse cards.
6. **Responsive.** Works on desktop (primary) and mobile web (secondary). Not a native app.

### 9.3 Page Specifications

#### 9.3.1 My Library (Browse View)
- Default: grid of cards with cover image placeholder, title, author/creator, format badge
- Filtering sidebar: format, genre, publisher, location, owner, shelf, read status
- Sort options: title (alpha), date added, year published, author
- Search bar with instant results
- View toggle: grid view (visual) / list view (dense table — for the spreadsheet feeling)
- Format-specific grouping: "Novels", "Comics", "Graphic Novels", "Non-fiction", "Magazines" as filterable tabs or chips

#### 9.3.2 Stories & Series (Browse View)
- Collections shown as a hierarchical tree or expandable cards
- Story Arcs shown as timelines with issue positions
- Volume Runs shown as horizontal scrollable strips of issue thumbnails
- Completion indicators: "You have 11 of 19 parts" with visual progress

#### 9.3.3 Artifact Detail Page
- **Hero section:** Cover image (large) + title + format badge + publisher + year
- **Metadata block:** ISBN, size, condition, location, owner, date added
- **Reprint lineage:** If reprint: "Reprints: [Original Volume] #[O#] ([Original Publisher], [Year])" with link to the Work
- **Contents section:** "What's Inside" — ordered list of Works contained, each clickable
- **Activity section:** Per-profile reading status and ratings
- **Physical section:** Copy information — location, condition. If lent: borrower name and date
- **Notes section:** Editable
- **Data provenance:** Subtle indicators for scraped fields. Small info icon showing source
- **Edit controls:** Inline editing or edit button
- **Danger zone (collapsed by default):** is_pirated toggle, delete button. Delete requires a two-step confirmation: click Delete → modal appears saying "Are you sure you want to delete [Title]? This cannot be undone." with a red confirm button. This is a soft-delete (mark inactive, recoverable by admin), but the UX should treat it as permanent to prevent casual deletion.

#### 9.3.4 Work Detail Page
- **Hero section:** Title + original publication year + work type badge
- **Creators:** Listed by role (Written by, Art by, etc.) — each clickable
- **Series position:** "Book 2 of 7 in Foundation" with Prev/Next links
- **Story arc position:** "Part 9 of 19 in Knightfall" with Prev/Next links + link to arc page
- **Volume run:** "Originally published in Batman Vol 1 #455" with link
- **"In Your Library" section:** All Artifacts containing this Work, with format, publisher, condition
- **External links:** Goodreads, ComicVine
- **Activity section:** Ratings and reading history per profile
- **Notes**

#### 9.3.5 Collection / Series Detail Page
- **Hero:** Series name + description
- **Work list:** Ordered by sequence number. Each work shows: title, year, format badges for owned artifacts, reading status indicators
- **Completion visual:** "5 of 7 books owned" progress bar
- **Sub-collections:** If nested (universe → series), show children

#### 9.3.6 Story Arc Detail Page
- **Hero:** Arc name + total parts
- **Reading order:** Ordered list of Works by arc position, showing which Volume Run each comes from (important for cross-title arcs like Knightfall)
- **Sub-arcs:** If nested, show expandable sections
- **Completion:** "You have 11 of 19 parts"

#### 9.3.7 Creator Detail Page (Phase 2)
- Name + aliases
- Works grouped by role (Written, Art, etc.), each group sorted by year
- Total count of owned artifacts featuring this creator

#### 9.3.8 Profile Selector
- Netflix-style profile picker on app launch: Utsav, Utkarsh, Som
- Simple avatar + name, no authentication (Phase 1)
- Selected profile shown in header, affects Activity Ledger entries
- Admin/edit capabilities available to all profiles initially

#### 9.3.9 Review Queue
- Accessible from a nav icon (subtle badge count for open flags)
- List of data quality flags, sortable by type
- Each flag shows: entity link, flag type, description, suggested fix
- Actions: Resolve (apply fix), Dismiss (ignore), Edit (go to entity)

### 9.4 Sample Data Pack for Stitch

A curated JSON dataset should be created containing ~40-50 items that exercise all entity types and edge cases. Include:

- 5-8 novels (mix of series and standalone, at least one with rating, one marked "Lent")
- 2-3 non-fiction (one narrative, one coffee table)
- 1 Hindi book
- 2 magazines
- 5-8 graphic novels (mix of original and reprint, one with complex Collects)
- 10-15 comic issues (include: one Knightfall arc sequence, one dual-story issue, one serialized/soap opera run, mix of Gotham reprints and originals, one Indian comic)
- 5-8 creators (at least one appearing as both novelist and comic writer)
- 2-3 collections (one nested)
- 2-3 story arcs (one nested: Knightfall with sub-arcs)
- Sample activity ledger entries
- Sample data quality flags

This data pack should be generated from the actual migrated database, not invented. The migration script should include a command to export this subset.

---

## 10. Scraping & Enrichment Workflow (Phase 2+)

### 10.1 Principle: User-Curated Data Is Sacred
Scraped data is a suggestion. It never overwrites user data silently. Every scraped field carries provenance metadata in the `field_provenance` table.

### 10.2 Sources
- **Comics:** ComicVine API (free for non-commercial use, rate-limited)
- **Novels:** OpenLibrary API (free, open source) and/or Google Books API
- **Audiobooks (later):** Audible scraping or manual entry
- **Cover images:** Multiple sources depending on format

### 10.3 User Flow

**Step 1: Trigger**
User clicks "Enrich" on an Artifact detail page, or selects multiple Artifacts for bulk enrichment.

**Step 2: Match Confirmation**
System searches the relevant API and presents candidates:
```
We found a possible match:
  Your entry: "Batman #7" (Americom/Gotham Comics)
  ComicVine: "Batman #455 — Identity Crisis, Part One" (DC Comics, 1991)
  
  [✓ Correct Match]  [✗ Wrong Match]  [Search Again with different terms]
```
If multiple candidates: show a short list with disambiguating info (year, publisher, cover thumbnail). User picks one.

**Step 3: Diff Review**
Side-by-side comparison:
```
                    Your Data              ComicVine
Title:              Batman #7              Batman #455 — Identity Crisis Part 1
Writer:             Grant, Alan            Alan Grant  ✓ (same person detected)
Cover Image:        [none]                 [thumbnail]  □ Accept
Original Year:      [empty]                1991         □ Accept
Synopsis:           [empty]                "Batman..."  □ Accept
```

Controls: **Accept All** | **Accept Selected** | **Reject All**

**Step 4: Conflict Resolution**
For fields with existing user data that differs from scraped:
```
Publisher:  Americom [yours]  vs  DC Comics [ComicVine]
[Keep Mine]  [Use Theirs]  [Keep Both as Note]
```

**Step 5: Apply**
Accepted fields are written to DB. Each gets a `field_provenance` record with `source=scraped:comicvine` and `approved=true`. In the UI, these fields show a subtle provenance indicator (small dot or icon) that reveals the source on hover.

**Step 6: Bulk Enrichment (Later)**
For "enrich everything":
- Run matching in background
- Produce review queue: "47 matched, 12 conflicts, 8 no match"
- User works through queue at leisure
- Nothing applied until reviewed

### 10.4 Cover Image Handling (Phase 2+)
- Scraped covers are stored locally and tagged with source
- Users can upload their own cover photos (phone pictures of physical books)
- Smart processing for user-uploaded covers: auto-crop, perspective correction, color balancing (use a CV library or API)
- User-uploaded covers take precedence over scraped ones

### 10.5 ISBN Scanning (Phase 2+)
- Mobile web: use camera API to scan barcode
- Lookup ISBN via OpenLibrary/Google Books
- Pre-fill artifact creation form with scraped data
- User reviews and confirms before saving
- All fields tagged as scraped with source

---

## 11. Phased Build Plan

Each step below specifies: what to do, which tool to use, what to feed it as input, and what output to expect. Follow this sequentially.

---

### Phase 1A: Schema Design & PRD ✅ COMPLETE
- **What happened:** Architecture, schema, migration rules, UI brief, all documented in this PRD.
- **Tool used:** Claude Max (project chat)
- **Output:** This document (`ALEXANDRIA_CORE_PRD.md`)

---

### Phase 1B: Migration — Build the Database

**Step 1B-1: Build SQLAlchemy models + migration script**
- **Tool:** Claude Code
- **Input to provide:** Upload `ALEXANDRIA_CORE_PRD.md` + `Our_Library-3.xlsx` to a Claude Code session
- **Prompt guidance:** "Read the PRD (especially Sections 5 and 6). Build SQLAlchemy models matching the schema. Write a migration script that reads the xlsx and populates an SQLite database. The script must produce a `migration_report.json` and populate the `data_quality_flags` table. Also export a sample data JSON per the spec in Section 12."
- **Expected output:** 
  - `models.py` (SQLAlchemy models)
  - `migrate.py` (migration script)
  - `alexandria.db` (populated SQLite database)
  - `migration_report.json` (counts, parse results, flagged items)
  - `sample_data.json` (curated subset for Stitch)
  - `CHANGELOG.md` and `DECISIONS.md` (as specified in Section 14)
- **Your review:** Check migration_report.json. Look at flagged items. Spot-check a few records in the DB (use a SQLite browser or ask Claude Code to run verification queries).

**Step 1B-2: Red Teamer validation**
- **Tool:** A SEPARATE Claude Code or Claude Max session (must not see the migration script code)
- **Input to provide:** Upload `ALEXANDRIA_CORE_PRD.md` (specifically Section 7) + `Our_Library-3.xlsx` + `alexandria.db` + `migration_report.json`
- **Prompt guidance:** "You are a migration validation agent. Read Section 7 of the PRD. You must NOT see the migration script code. Validate that the migration from the xlsx to the SQLite database was lossless and semantically correct. Run all 6 validation layers. Produce the JSON output specified in Section 7.3."
- **Expected output:** `validation_report.json` with PASS/FAIL per layer
- **Your review:** If any layer fails, take the failure report back to the Step 1B-1 Claude Code session for fixes, then re-run validation.

**Step 1B-3: Fix flagged data quality issues**
- **Tool:** Claude Max (project chat) or Claude Code — your choice
- **Input:** `data_quality_flags` from the DB, plus the validation report
- **Action:** Review flagged items (unparsed Collects, potential duplicate creators, etc.). Decide resolutions. Apply fixes either by editing the DB directly or by re-running migration with corrections.
- **This is a human-in-the-loop step.** You and Utkarsh should review the flags together — you know your collection best.

---

### Phase 1C: UI Exploration

**Step 1C-1: Generate design prototypes**
- **Tool:** Google Stitch (Antigravity)
- **Input to provide:** Copy-paste Section 9 (UI/UX Requirements) from this PRD as the prompt context. Also provide `sample_data.json` from Step 1B-1.
- **Prompt guidance:** "Design a personal library web app. Here are the UX requirements [paste Section 9]. Here is sample data from the real library [attach sample_data.json]. Build: (1) A My Library browse view with cover image cards, filtering, and format tabs. (2) An Artifact detail page. (3) A Work detail page. Make it feel like a personal museum — pride and warmth, not a corporate admin panel. Responsive for desktop and mobile."
- **Expected output:** Interactive prototypes / component designs
- **Decision point:** If Stitch produces functional, data-connected components → continue using Stitch for frontend. If it produces pretty but structurally broken output → use the visual designs as reference, implement in Claude Code (Phase 1E).

**Step 1C-2: Iterate on design**
- **Tool:** Google Stitch (Antigravity), same session
- **Action:** Iterate based on your reaction. Try different layouts for the browse view (grid vs. list). Try the detail page with comic issues vs. novels. Test on mobile viewport.
- **Output:** Finalized visual direction and component patterns (screenshots, exported code, or Stitch project link)

---

### Phase 1D: Backend API

**Step 1D-1: Build the FastAPI backend**
- **Tool:** Claude Code
- **Input to provide:** Upload `ALEXANDRIA_CORE_PRD.md` (specifically Section 8) + the `models.py` and `alexandria.db` from Step 1B-1
- **Prompt guidance:** "Read Section 8 of the PRD. The SQLAlchemy models and populated SQLite DB are already built [attach files]. Build a FastAPI backend implementing all the CRUD endpoints specified. Include the search endpoint, the data quality flag endpoints, and the lending workflow. The API must automatically update the `reading_status` cache table when Activity Ledger events are written. Write test cases for the critical endpoints (especially dual-story artifact retrieval, story arc navigation, creator deduplication merge, and lending flow)."
- **Expected output:**
  - `main.py` (FastAPI app)
  - `routers/` directory with endpoint modules
  - `tests/` directory with test cases
  - Updated `CHANGELOG.md`
- **Your review:** Ask Claude Code to run the test suite. Verify a few API calls manually (e.g., GET an artifact you know has two stories, check the response structure).

**Step 1D-2: Propose and run test cases**
- **Tool:** Same Claude Code session
- **Action:** Claude Code should propose test cases BEFORE implementing them. You review and approve. Then they run.
- **Critical test cases that must be included:**
  - Retrieve a dual-story Gotham issue → verify both Works returned with correct positions
  - Retrieve a Knightfall arc → verify cross-volume reading order
  - Create a new artifact with only title + format → verify it succeeds with all other fields null
  - Lend a copy → verify borrower_name and location updated
  - Return a copy → verify lending info cleared
  - Merge two duplicate creators → verify all their roles transfer to the surviving record
  - Write an Activity Ledger event → verify reading_status cache is updated

---

### Phase 1E: Frontend Implementation

**Step 1E-1: Build the React frontend**
- **Tool:** Claude Code
- **Input to provide:** Upload `ALEXANDRIA_CORE_PRD.md` (Section 9) + Stitch design outputs from Phase 1C (screenshots, exported components, or design descriptions) + the running API from Phase 1D
- **Prompt guidance:** "Read Section 9 of the PRD. Here are the UI designs from Stitch [attach]. Build a React + Tailwind + shadcn/ui frontend that implements these designs with real API data bindings. Build these pages: (1) My Library browse with grid/list toggle, filtering, search. (2) Artifact detail page. (3) Work detail page. (4) Collection/Series detail page. (5) Story Arc detail page. (6) Profile selector (Netflix-style). (7) Review Queue for data quality flags. (8) Inline editing on detail pages. Make it responsive for desktop and mobile."
- **Expected output:** Complete React application
- **Your review:** Test all page types with real data. Specifically test:
  - A Gotham reprint issue → does the reprint lineage display correctly?
  - A Knightfall arc issue → does the Prev/Next navigation work across volumes?
  - A novel with ratings → do Uts* and Utk* ratings show correctly?
  - Mobile viewport → is it usable?
  - Create a new book with just title + format → does the minimal creation flow work?

---

### Phase 2 (Later — scope only, no tool routing yet)
- Kindle and Audible collection import
- ISBN barcode scanning
- Cover image scraping from ComicVine/OpenLibrary
- User cover photo upload with smart crop/color correction
- Creator detail pages (People tab as third navigation entry)
- Authentication (admin password for edit, open for browse)
- Read-only sharing view for friends
- Pretext.js integration for dense virtual scrolling

### Phase 3 (Later)
- Enrichment engine: ComicVine, OpenLibrary, Google Books API integration
- Full scraping approval workflow (Section 10)
- Bulk enrichment with review queue
- Friend comments/ratings on shared view

### Phase 4 (Later)
- Gap tracker / Gotham Checklist feature (rebuilt from spreadsheet concept)
- Reading statistics and visualizations
- Export capabilities
- theGoodICBMstock: Indian comic book cataloging side project (separate scope)

---

## 12. Sample Data for UI Prototyping

The migration script (Phase 1B) should export a JSON file containing a representative subset for Stitch. Below is the specification of what to include. **Do not invent data — extract from the actual migrated database.**

### Required Samples:

**Novels (5-8):**
- One from a series with sequence number (e.g., Foundation #2)
- One standalone (e.g., To Kill a Mockingbird)
- One with both Uts* and Utk* ratings
- One marked "Lent"
- One with translator

**Non-fiction (2-3):**
- One with Story=Yes (narrative non-fiction)
- One with Coffee Table=Yes

**Hindi Book (1)**

**Magazines (2):**
- One with a date, one without (Comic Jump)

**Graphic Novels (5-8):**
- One original (e.g., Watchmen)
- One Gotham reprint with clear Collects mapping
- One with complex Collects (flagged for review)
- One from an Indian creator (e.g., Adi Parva)
- One from a series (e.g., Parva Duology)

**Comic Issues (10-15):**
- A sequence from the Knightfall arc (4-5 issues across Batman and Detective Comics)
- One dual-story issue (e.g., Amazing Spider-Man #3 Gotham)
- One serialized/soap opera run issue (e.g., Avengers Gotham)
- One Indian original (e.g., Ravanayan)
- One with notes containing editorial observations

**Creators (5-8):**
- Neil Gaiman (novelist + comic writer if applicable)
- Alan Grant (comic writer across multiple volumes)
- At least one artist who appears on multiple issues
- At least one writer-artist combo (e.g., Mike Mignola)

**Collections (2-3):**
- One simple series (Foundation)
- One nested if applicable

**Story Arcs (2-3):**
- Knightfall (with sub-arcs: The Crusade, The Search, KnightsEnd)
- One simple arc (Identity Crisis)

**Activity Ledger entries (5-10):**
- Mix of ratings and read events across profiles

**Data Quality Flags (3-5):**
- One missing ISBN
- One unparsed Collects
- One name inconsistency

---

## 13. Decision Log

All architectural and design decisions made during the planning phase, with rationale.

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| D-001 | 2026-04-02 | Use FRBR-inspired two-level model (Work + Artifact) rather than full four-level FRBR | Full FRBR (Work → Expression → Manifestation → Item) is overkill for ~1K items. Two levels plus a Copies table covers all cases. Expression-level differences (recoloring, censored panels) captured in notes. | Approved |
| D-002 | 2026-04-02 | Backend stack: Python + FastAPI + SQLAlchemy + SQLite | Most LLM-maintainable stack. Python readable for owner's background. SQLite appropriate for scale. | Approved |
| D-003 | 2026-04-02 | Frontend stack: React + Tailwind + shadcn/ui | Standard, well-supported by Stitch and Claude Code. Design quality comes from the design layer, not the framework. | Approved |
| D-004 | 2026-04-02 | Stitch-first iterative UI approach | Start with Stitch for design exploration. If components are functional, keep using Stitch. If not, use as visual reference and implement in Claude Code. | Approved |
| D-005 | 2026-04-02 | Separate narrative_format from completion_status | Original spreadsheet's `Complete` column overloaded `S` (soap opera structure) with `Y/N` (collection completeness). These are distinct dimensions that correlate but should be independent fields. `S` maps to BOTH `narrative_format=Serialized` AND `completion_status=Not Pursuing`. | Approved |
| D-006 | 2026-04-02 | Genre stays on Artifact for Phase 1 | main_genre and sous_genre came from the Novel sheet at the book level. Could migrate to Work level or become a tagging system later. Keeping on Artifact for now to preserve source data fidelity. | Approved — revisit in Phase 2 |
| D-007 | 2026-04-02 | Data quality flags as non-intrusive review queue | Flags surface in a dedicated Review Queue page, not as pop-ups or blocking alerts. Users process at their leisure. Prevents alert fatigue. | Approved |
| D-008 | 2026-04-02 | Scraping approval workflow: match first, then diff review | Never auto-apply scraped data. User confirms match (is this the right book?), then selectively approves individual fields. Prevents data corruption from bad API matches. | Approved |
| D-009 | 2026-04-02 | All scraped fields tagged with source and approval status | field_provenance table tracks source for every scraped field. UI shows subtle indicator. User-entered data is never overwritten without explicit consent. | Approved |
| D-010 | 2026-04-02 | Minimal required fields for item creation: title + format only | Low barrier to entry. Everything else optional, fillable later via scraping or manual edit. | Approved |
| D-011 | 2026-04-02 | is_pirated kept as boolean | Simple flag. UI hides entirely when false. Shows subtle icon on detail page only when true. Not shown on browse/card views. | Approved |
| D-012 | 2026-04-02 | Ownership is binary: "The Bansal Brothers" or "Somdutta" | Not per-individual. Profiles (Utsav/Utkarsh/Som) are for Activity Ledger only, not ownership. | Approved |
| D-013 | 2026-04-02 | Magazine dates: keep empty when unknown | Comic Jump and some other magazines have no discoverable publication dates. Don't flag these as quality issues. | Approved |
| D-014 | 2026-04-02 | GR* (Goodreads community rating) not migrated | This is third-party aggregate data, not user data. Can be re-fetched via API in enrichment phase. | Approved |
| D-015 | 2026-04-02 | Collects parsing: auto-parse simple cases, flag complex for review | Regex handles "Title #X-Y" patterns. Complex cases (partial issues, multiple series) flagged as data_quality_flags for manual resolution. Owner can change this approach later. | Approved — owner may revisit |
| D-016 | 2026-04-02 | Story arcs support nesting via self-referencing parent | Knightfall → Knightquest: The Crusade is modeled as parent/child arcs. Supports arbitrary depth. | Approved |
| D-017 | 2026-04-02 | Copies table for duplicate physical items | Most items have 1 copy (auto-created). Rare duplicates get additional rows. Each copy has independent location, condition, borrower info. | Approved |
| D-018 | 2026-04-02 | date_added field on Artifacts | Tracks when a book was added to the library. Migrated items default to migration date. New items set automatically. | Approved |
| D-019 | 2026-04-02 | Pretext.js deferred to Phase 2+ | Relevant for performance optimization of dense browse views. Not a framework choice — a layout acceleration library. Use when item count and visual density justify it. | Approved |
| D-020 | 2026-04-02 | Gap tracker / Checklist deferred to Phase 3-4 | Gotham Checklist functionality is useful but not immediate. Rebuild as app feature later. | Approved |
| D-021 | 2026-04-02 | ComicVine API for comics enrichment | Free for non-commercial use. Rate limited but sufficient for personal library. Prefer API over scraping. | Approved |
| D-022 | 2026-04-02 | Add internal_sku to Copies table | Nullable field for future physical copy identification (spine labels, NFC stickers, QR codes). Costs nothing now, solves a real problem when distinguishing duplicate copies. Suggested by external review. | Approved |
| D-023 | 2026-04-02 | Add volume_number (integer) to volume_runs | ComicVine indexes volumes by integer sequence. Having this field makes Phase 3 API matching significantly more accurate. Suggested by external review. | Approved |
| D-024 | 2026-04-02 | Migration script must not hardcode dual-story column patterns | The `artifact_works` join table supports N works per artifact. The migration script should dynamically detect columns matching `Original Volume Issue N` patterns rather than hardcoding "2". Suggested by external review. | Approved |
| D-025 | 2026-04-02 | Add reading_status denormalized cache table | Avoids scanning full Activity Ledger to determine current reading state for browse views. Updated automatically when ledger events are written. Ledger remains source of truth. Suggested by external review. | Approved |
| D-026 | 2026-04-02 | Delete uses two-step confirmation modal, not type-to-confirm | Personal app with 3 users doesn't need type-the-title friction. Red button in confirmation modal is sufficient. Underlying operation is soft-delete anyway. Modified from external review suggestion. | Approved |
| D-027 | 2026-04-02 | REJECTED: Synthetic date staggering for migrated items | Manufacturing fake dates from row order creates false historical metadata that looks real. Row order in the spreadsheet is alphabetical-by-author, not chronological. Honest migration-date timestamps are better than plausible-looking lies. Users can manually backfill real dates later. | Rejected |
| D-028 | 2026-04-02 | Move completion_status (Y/N) from volume_runs to story_arcs | Owner clarified that Y/N in Complete column is per-story-arc ("I own all issues in this arc") not per-volume-run. Mixed Y/N within a volume run is correct data representing different arcs at different completion levels. Majority-vote aggregation to volume_runs destroyed per-arc information and generated 24 spurious conflicting_data flags. S (Serialized/Not Pursuing) correctly stays on volume_runs. Discovered during Red Teamer validation (Phase 1B-2). Corrects PRD v1.0 error in Sections 5.2 and 6.3.6. | Approved |

---

## 14. Notes for AI Agent Developers

### 14.1 For Claude Code (Backend & Migration)

- **Read this entire PRD before writing code.** The schema in Section 5 is authoritative. Do not deviate without discussing with the product owner.
- **The source file `Our_Library-3.xlsx` is in this project's uploads.** Read it using pandas. Be careful with the ` Year` column (leading space in header).
- **Test the migration against the Red Teamer spec (Section 7).** Write the migration to produce a `migration_report.json` that the red teamer can validate.
- **Maintain a CHANGELOG.md** in the project root. Log every significant code change with date and reason.
- **Maintain a DECISIONS.md** alongside this PRD. When implementation requires decisions not covered here, document them with rationale and flag for product owner review.
- **Code style:** Clear variable names, docstrings on all functions, type hints everywhere. The owner has a CS background but hasn't coded recently — readability matters more than cleverness.
- **Test cases:** Propose test cases before implementing. Get approval. Run all tests before committing. Include edge cases from Section 7.4.

### 14.2 For Google Stitch / Antigravity (UI Exploration)

- **Read Section 9 (UI/UX Requirements) thoroughly.** The emotional brief matters as much as the feature list.
- **Use the sample data JSON** generated from Phase 1B. Don't invent fake data — use real entries from the library.
- **Design for three page types first:** Browse grid (My Library), Artifact detail page, Work detail page. These are the core experience.
- **The "shelf" feeling is essential.** Cover image placeholders should be prominent even without real covers. Think bookshop display, not spreadsheet.
- **Cross-linking is a first-class feature.** Every creator name, series, arc, publisher should look clickable and be clickable.
- **Responsive:** Desktop-first but must degrade gracefully to mobile web.

### 14.3 For Red Teamer Agent (Migration Validation)

- **You must NOT have access to the migration script code.** You validate outputs only.
- **Follow Section 7 exactly.** Produce the JSON output format specified.
- **Be adversarial.** Assume the migration script has bugs. Your job is to find them.
- **Pay special attention to:** float-to-string ISBN conversion, dual-story issue linking, story arc parenthetical parsing, creator deduplication across sheets, the `S`→Serialized mapping.

### 14.4 Decision Log and Changelog for All Agents

Every AI agent working on this project should:
1. Read this PRD before starting any work
2. Check DECISIONS.md for any updates since this PRD was written
3. Log their own decisions in DECISIONS.md if they make choices not covered here
4. Log code changes in CHANGELOG.md
5. Flag anything that contradicts this PRD for product owner review rather than silently resolving it

---

*End of PRD. Document hash should be recorded by the implementing agent for version tracking.*
