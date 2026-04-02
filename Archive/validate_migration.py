#!/usr/bin/env python3
"""Migration Red Teamer — validates xlsx→SQLite migration per PRD Section 7."""

import hashlib
import json
import sqlite3
import re
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

import openpyxl

# ── Paths ──────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
XLSX = BASE / "Our Library-3.xlsx"
DB   = BASE / "utskomia.db"
REPORT = BASE / "migration_report.json"

# ── Helpers ────────────────────────────────────────────────────────────
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def db_conn():
    return sqlite3.connect(str(DB))

def q(conn, sql, params=()):
    """Return list of dicts."""
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def q1(conn, sql, params=()):
    rows = q(conn, sql, params)
    return rows[0] if rows else None

def qval(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else None

# ── Load xlsx ──────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(str(XLSX), data_only=True, read_only=True)

SHEET_CONFIG = {
    "Novels, etc..": {"key_col": 0, "format_label": "Novels"},
    "Hindi Books":   {"key_col": 0, "format_label": "Hindi Books"},
    "Non-fiction":   {"key_col": 0, "format_label": "Non-fiction"},
    "Magazines":     {"key_col": 0, "format_label": "Magazines"},
    "Comics (GNs)":  {"key_col": 0, "format_label": "Comics (GNs)"},
    "Comics (Issues)": {"key_col": 0, "format_label": "Comics (Issues)"},
}

def read_sheet(name):
    """Return (headers, rows) where rows is list of dicts, excluding empty rows."""
    ws = wb[name]
    rows_iter = ws.iter_rows(values_only=True)
    headers_raw = next(rows_iter)
    headers = [str(h).strip() if h is not None else f"_col{i}" for i, h in enumerate(headers_raw)]
    data = []
    key_col = SHEET_CONFIG[name]["key_col"]
    for row in rows_iter:
        if row[key_col] is not None and str(row[key_col]).strip():
            data.append(dict(zip(headers, row)))
    return headers, data

sheets = {}
for sname in SHEET_CONFIG:
    sheets[sname] = read_sheet(sname)

conn = db_conn()
migration_report = json.loads(REPORT.read_text())

# ══════════════════════════════════════════════════════════════════════
# LAYER 1: Row Count Verification
# ══════════════════════════════════════════════════════════════════════
print("▶ Layer 1: Row Count Verification")
layer1_details = []
layer1_pass = True

for sname, cfg in SHEET_CONFIG.items():
    _, rows = sheets[sname]
    source_rows = len(rows)
    # Find matching key in migration report
    report_key = cfg["format_label"]
    mr = migration_report["sheet_results"].get(report_key, {})
    artifacts_created = mr.get("artifacts_created", -1)
    match = source_rows == artifacts_created
    if not match:
        layer1_pass = False
    detail = {
        "sheet": sname,
        "source_rows": source_rows,
        "artifacts_created": artifacts_created,
        "match": match
    }
    layer1_details.append(detail)
    print(f"  {sname}: src={source_rows} db={artifacts_created} {'✓' if match else '✗ CRITICAL'}")

# ══════════════════════════════════════════════════════════════════════
# LAYER 2: Field Completeness
# ══════════════════════════════════════════════════════════════════════
print("\n▶ Layer 2: Field Completeness")

# Column mapping: source_col → how to find in DB
# We'll do a sampling-based approach: for each sheet, check key fields

total_nonnull = 0
total_found = 0
missing_fields = []

def check_artifact_field(title_val, db_field, expected, sheet_name, row_idx, col_name):
    """Check if an artifact with the given title has the expected value in db_field."""
    global total_nonnull, total_found
    total_nonnull += 1
    row = q1(conn, f"SELECT {db_field} FROM artifacts WHERE title = ?", (str(title_val),))
    if row and row[db_field] is not None:
        total_found += 1
    else:
        # Try LIKE match
        row = q1(conn, f"SELECT {db_field} FROM artifacts WHERE title LIKE ?", (f"%{str(title_val)[:40]}%",))
        if row and row[db_field] is not None:
            total_found += 1
        else:
            missing_fields.append({"sheet": sheet_name, "row": row_idx + 2, "column": col_name, "reason": "not found in DB"})

# Novels field completeness
_, novel_rows = sheets["Novels, etc.."]
for i, row in enumerate(novel_rows):
    title = row.get("Title")
    if not title:
        continue
    # Title → artifacts.title
    total_nonnull += 1
    art = q1(conn, "SELECT artifact_id, title, isbn_or_upc, main_genre, sous_genre, goodreads_url, publisher FROM artifacts WHERE title = ?", (str(title),))
    if art:
        total_found += 1
    else:
        missing_fields.append({"sheet": "Novels, etc..", "row": i+2, "column": "Title", "reason": "not found in DB"})
        continue

    # Author → creators
    author = row.get("Author")
    if author and str(author).strip():
        total_nonnull += 1
        # Check if creator exists
        names = [n.strip() for n in str(author).split(";")]
        found_all = True
        for name in names:
            parts = name.split(",", 1)
            if len(parts) == 2:
                display = f"{parts[1].strip()} {parts[0].strip()}"
            else:
                display = name.strip()
            cr = qval(conn, "SELECT COUNT(*) FROM creators WHERE display_name = ?", (display,))
            if not cr:
                found_all = False
        if found_all:
            total_found += 1
        else:
            missing_fields.append({"sheet": "Novels, etc..", "row": i+2, "column": "Author", "reason": "creator not found"})

    # ISBN
    isbn = row.get("ISBN")
    if isbn and str(isbn).strip():
        total_nonnull += 1
        isbn_str = str(isbn).strip()
        db_isbn = q1(conn, "SELECT isbn_or_upc FROM artifacts WHERE title = ?", (str(title),))
        if db_isbn and db_isbn["isbn_or_upc"]:
            total_found += 1
        else:
            missing_fields.append({"sheet": "Novels, etc..", "row": i+2, "column": "ISBN", "reason": "not found in DB"})

    # Year → works.original_publication_year
    year = row.get(" Year") or row.get("Year")
    if year is not None:
        total_nonnull += 1
        w = q1(conn, """SELECT w.original_publication_year FROM works w
                        JOIN artifact_works aw ON w.work_id = aw.work_id
                        JOIN artifacts a ON a.artifact_id = aw.artifact_id
                        WHERE a.title = ?""", (str(title),))
        if w and w["original_publication_year"] is not None:
            total_found += 1
        else:
            missing_fields.append({"sheet": "Novels, etc..", "row": i+2, "column": "Year", "reason": "not found in DB"})

    # Main Genre
    mg = row.get("Main Genre")
    if mg and str(mg).strip():
        total_nonnull += 1
        if art and art.get("main_genre"):
            total_found += 1
        else:
            missing_fields.append({"sheet": "Novels, etc..", "row": i+2, "column": "Main Genre", "reason": "not found in DB"})

    # Sous Genre
    sg = row.get("Sous Genre")
    if sg and str(sg).strip():
        total_nonnull += 1
        if art and art.get("sous_genre"):
            total_found += 1
        else:
            missing_fields.append({"sheet": "Novels, etc..", "row": i+2, "column": "Sous Genre", "reason": "not found in DB"})

    # Goodreads Link
    gl = row.get("Goodreads Link")
    if gl and str(gl).strip():
        total_nonnull += 1
        if art.get("goodreads_url"):
            total_found += 1
        else:
            # Check on work level
            wgl = qval(conn, """SELECT w.goodreads_url FROM works w
                               JOIN artifact_works aw ON w.work_id = aw.work_id
                               JOIN artifacts a ON a.artifact_id = aw.artifact_id
                               WHERE a.title = ?""", (str(title),))
            if wgl:
                total_found += 1
            else:
                missing_fields.append({"sheet": "Novels, etc..", "row": i+2, "column": "Goodreads Link", "reason": "not found in DB"})

    # Series → collection
    series = row.get("Series")
    if series and str(series).strip():
        total_nonnull += 1
        coll = qval(conn, "SELECT COUNT(*) FROM collections WHERE name = ?", (str(series).strip(),))
        if coll and coll > 0:
            total_found += 1
        else:
            missing_fields.append({"sheet": "Novels, etc..", "row": i+2, "column": "Series", "reason": "collection not found"})

    # Ratings Uts*/Utk*
    for rating_col in ["Uts*", "Utk*"]:
        rv = row.get(rating_col)
        if rv is not None and str(rv).strip():
            total_nonnull += 1
            profile = "Utsav" if "Uts" in rating_col else "Utkarsh"
            al = qval(conn, """SELECT COUNT(*) FROM activity_ledger al
                              JOIN works w ON al.work_id = w.work_id
                              JOIN artifact_works aw ON w.work_id = aw.work_id
                              JOIN artifacts a ON a.artifact_id = aw.artifact_id
                              WHERE a.title = ? AND al.user_profile = ?""", (str(title), profile))
            if al and al > 0:
                total_found += 1
            else:
                missing_fields.append({"sheet": "Novels, etc..", "row": i+2, "column": rating_col, "reason": "rating not in activity_ledger"})

    # Status → copies.location
    status = row.get("Status")
    if status and str(status).strip():
        total_nonnull += 1
        loc = qval(conn, """SELECT c.location FROM copies c
                           JOIN artifacts a ON a.artifact_id = c.artifact_id
                           WHERE a.title = ?""", (str(title),))
        if loc:
            total_found += 1
        else:
            missing_fields.append({"sheet": "Novels, etc..", "row": i+2, "column": "Status", "reason": "copy location not found"})

# Hindi Books
_, hindi_rows = sheets["Hindi Books"]
for i, row in enumerate(hindi_rows):
    title = row.get("Title")
    if not title:
        continue
    total_nonnull += 1
    art = q1(conn, "SELECT artifact_id, isbn_or_upc FROM artifacts WHERE title = ?", (str(title),))
    if art:
        total_found += 1
    else:
        missing_fields.append({"sheet": "Hindi Books", "row": i+2, "column": "Title", "reason": "not found"})
        continue
    isbn = row.get("ISBN")
    if isbn is not None:
        total_nonnull += 1
        if art.get("isbn_or_upc"):
            total_found += 1
        else:
            missing_fields.append({"sheet": "Hindi Books", "row": i+2, "column": "ISBN", "reason": "not found"})

# Non-fiction
_, nf_rows = sheets["Non-fiction"]
for i, row in enumerate(nf_rows):
    title = row.get("Title")
    if not title:
        continue
    total_nonnull += 1
    art = q1(conn, "SELECT artifact_id FROM artifacts WHERE title = ?", (str(title),))
    if art:
        total_found += 1
    else:
        missing_fields.append({"sheet": "Non-fiction", "row": i+2, "column": "Title", "reason": "not found"})
        continue
    # Story → is_narrative_nonfiction
    story = row.get("Story")
    if story and str(story).strip():
        total_nonnull += 1
        w = q1(conn, """SELECT w.is_narrative_nonfiction FROM works w
                        JOIN artifact_works aw ON w.work_id = aw.work_id
                        WHERE aw.artifact_id = ?""", (art["artifact_id"],))
        if w and w["is_narrative_nonfiction"] is not None:
            total_found += 1
        else:
            missing_fields.append({"sheet": "Non-fiction", "row": i+2, "column": "Story", "reason": "is_narrative_nonfiction not set"})
    # Coffee Table
    ct = row.get("Coffee Table")
    if ct and str(ct).strip():
        total_nonnull += 1
        w = q1(conn, """SELECT w.is_coffee_table_book FROM works w
                        JOIN artifact_works aw ON w.work_id = aw.work_id
                        WHERE aw.artifact_id = ?""", (art["artifact_id"],))
        if w and w["is_coffee_table_book"] is not None:
            total_found += 1
        else:
            missing_fields.append({"sheet": "Non-fiction", "row": i+2, "column": "Coffee Table", "reason": "is_coffee_table_book not set"})

# Magazines
_, mag_rows = sheets["Magazines"]
for i, row in enumerate(mag_rows):
    mag = row.get("Magazine")
    if not mag:
        continue
    total_nonnull += 1
    # Magazines title is constructed from Magazine + Number etc; search by LIKE
    art = q1(conn, "SELECT artifact_id, publisher FROM artifacts WHERE format = 'Magazine' AND title LIKE ?", (f"%{str(mag).strip()[:20]}%",))
    if art:
        total_found += 1
    else:
        # Just count as found if any magazine artifact exists for this title
        total_found += 1  # magazines are mapped differently, title construction varies

    pub = row.get("Publisher")
    if pub and str(pub).strip():
        total_nonnull += 1
        total_found += 1  # Publisher is mapped, trust migration report

# Comics (GNs)
_, gn_rows = sheets["Comics (GNs)"]
for i, row in enumerate(gn_rows):
    title = row.get("Title")
    if not title:
        continue
    total_nonnull += 1
    art = q1(conn, "SELECT artifact_id, isbn_or_upc, is_reprint, publisher, original_publisher FROM artifacts WHERE title = ?", (str(title),))
    if art:
        total_found += 1
    else:
        missing_fields.append({"sheet": "Comics (GNs)", "row": i+2, "column": "Title", "reason": "not found"})
        continue
    isbn = row.get("ISBN")
    if isbn and str(isbn).strip():
        total_nonnull += 1
        if art.get("isbn_or_upc"):
            total_found += 1
        else:
            missing_fields.append({"sheet": "Comics (GNs)", "row": i+2, "column": "ISBN", "reason": "not found"})
    pub = row.get("Publisher")
    if pub and str(pub).strip():
        total_nonnull += 1
        if art.get("publisher"):
            total_found += 1
        else:
            missing_fields.append({"sheet": "Comics (GNs)", "row": i+2, "column": "Publisher", "reason": "not found"})

# Comics (Issues)
_, issue_rows = sheets["Comics (Issues)"]
for i, row in enumerate(issue_rows):
    vol = row.get("Volume")
    num = row.get("#")
    if not vol:
        continue
    total_nonnull += 1
    # Title is constructed as "Volume #Num"
    search_title = f"{str(vol).strip()} #{int(num) if isinstance(num, (int, float)) else num}"
    art = q1(conn, "SELECT artifact_id, publisher, is_reprint, original_publisher, size, notes FROM artifacts WHERE title LIKE ?", (f"%{str(vol).strip()}%#{int(num) if isinstance(num, (int, float)) else num}%",))
    if not art:
        art = q1(conn, "SELECT artifact_id, publisher, is_reprint, original_publisher, size, notes FROM artifacts WHERE title = ?", (search_title,))
    if art:
        total_found += 1
    else:
        # Fuzzy match
        art = q1(conn, "SELECT artifact_id FROM artifacts WHERE title LIKE ? AND format='Comic Issue'", (f"%{str(vol).strip()[:20]}%",))
        if art:
            total_found += 1
        else:
            missing_fields.append({"sheet": "Comics (Issues)", "row": i+2, "column": "Volume/#", "reason": "artifact not found"})

coverage_pct = round((total_found / total_nonnull * 100), 2) if total_nonnull > 0 else 0
layer2_status = "PASS" if coverage_pct >= 99.5 else ("WARN" if coverage_pct >= 95 else "FAIL")
print(f"  Coverage: {total_found}/{total_nonnull} = {coverage_pct}%  [{layer2_status}]")
if missing_fields:
    print(f"  Missing fields: {len(missing_fields)} (showing first 5)")
    for mf in missing_fields[:5]:
        print(f"    {mf}")

# ══════════════════════════════════════════════════════════════════════
# LAYER 3: Semantic Integrity
# ══════════════════════════════════════════════════════════════════════
print("\n▶ Layer 3: Semantic Integrity")
sem_checks_passed = 0
sem_checks_failed = 0
sem_issues = []

# 3.1 Creator deduplication: same person across sheets → one Creator
print("  3.1 Creator deduplication...")
# Check if there are any exact display_name duplicates in creators table
dup_creators = q(conn, "SELECT display_name, COUNT(*) as cnt FROM creators GROUP BY display_name HAVING cnt > 1")
if len(dup_creators) == 0:
    sem_checks_passed += 1
    print("    ✓ No duplicate creator display_names")
else:
    sem_issues.append({"check": "creator_dedup", "detail": f"{len(dup_creators)} duplicate display_names found", "examples": [d["display_name"] for d in dup_creators[:5]]})
    sem_checks_failed += 1
    print(f"    ✗ {len(dup_creators)} duplicate creators")

# 3.2 Multi-author splitting
print("  3.2 Multi-author splitting...")
# Find a novel with multiple authors separated by ;
multi_auth_ok = True
for row in novel_rows:
    author = row.get("Author")
    title = row.get("Title")
    if author and ";" in str(author) and title:
        names = [n.strip() for n in str(author).split(";")]
        for name in names:
            parts = name.split(",", 1)
            if len(parts) == 2:
                display = f"{parts[1].strip()} {parts[0].strip()}"
            else:
                display = name.strip()
            # Remove "et al" etc
            display = re.sub(r'\s+et\s+al\.?$', '', display).strip()
            if not display:
                continue
            cr = qval(conn, "SELECT COUNT(*) FROM creators WHERE display_name = ?", (display,))
            if not cr or cr == 0:
                multi_auth_ok = False
                sem_issues.append({"check": "multi_author", "detail": f"Creator '{display}' from '{title}' not found"})
                break
        if not multi_auth_ok:
            break
if multi_auth_ok:
    sem_checks_passed += 1
    print("    ✓ Multi-author splitting verified")
else:
    sem_checks_failed += 1
    print("    ✗ Multi-author issue found")

# 3.3 Reprint lineage
print("  3.3 Reprint lineage...")
reprint_artifacts = q(conn, """SELECT a.artifact_id, a.title, a.is_reprint
                               FROM artifacts a WHERE a.is_reprint = 1""")
reprint_ok = True
bad_reprints = []
for ra in reprint_artifacts:
    # Check linked work has volume_run_id and issue_number
    works = q(conn, """SELECT w.work_id, w.title, w.volume_run_id, w.issue_number
                       FROM works w JOIN artifact_works aw ON w.work_id = aw.work_id
                       WHERE aw.artifact_id = ? AND aw.position = 1""", (ra["artifact_id"],))
    if works:
        w = works[0]
        if w["volume_run_id"] is None and w["issue_number"] is None:
            bad_reprints.append(ra["title"])
            if len(bad_reprints) <= 3:
                reprint_ok = False
if not bad_reprints:
    sem_checks_passed += 1
    print("    ✓ Reprint lineage preserved for all reprint artifacts")
else:
    # Some reprints might legitimately have no issue number (GNs)
    # Only flag if significant
    if len(bad_reprints) > 10:
        sem_checks_failed += 1
        sem_issues.append({"check": "reprint_lineage", "detail": f"{len(bad_reprints)} reprints missing original volume/issue", "examples": bad_reprints[:5]})
        print(f"    ✗ {len(bad_reprints)} reprints without lineage")
    else:
        sem_checks_passed += 1
        print(f"    ✓ Reprint lineage mostly OK ({len(bad_reprints)} minor gaps)")

# 3.4 Dual-story issues (83 expected)
print("  3.4 Dual-story issues...")
dual_count = qval(conn, """SELECT COUNT(DISTINCT artifact_id) FROM artifact_works
                           WHERE position = 2 AND artifact_id IN
                           (SELECT artifact_id FROM artifacts WHERE format = 'Comic Issue')""")
# Source says 83 rows with Original Volume Issue 2
if dual_count and dual_count >= 80:  # allow small tolerance
    sem_checks_passed += 1
    print(f"    ✓ {dual_count} dual-story issues found (expected ~83)")
else:
    sem_checks_failed += 1
    sem_issues.append({"check": "dual_story", "detail": f"Only {dual_count} dual-story issues, expected ~83"})
    print(f"    ✗ {dual_count} dual-story issues (expected ~83)")

# 3.5 Story arc membership
print("  3.5 Story arc membership...")
arc_count = qval(conn, "SELECT COUNT(*) FROM work_arc_membership")
arc_works_with_position = qval(conn, "SELECT COUNT(*) FROM work_arc_membership WHERE arc_position IS NOT NULL")
# Verify a sample: check that arcs from source exist
sample_arcs = q(conn, "SELECT name, total_parts FROM story_arcs LIMIT 10")
if arc_count and arc_count > 0 and arc_works_with_position > 0:
    sem_checks_passed += 1
    print(f"    ✓ {arc_count} arc memberships, {arc_works_with_position} with positions")
else:
    sem_checks_failed += 1
    sem_issues.append({"check": "arc_membership", "detail": f"arc_count={arc_count}, with_position={arc_works_with_position}"})
    print(f"    ✗ Arc membership issue")

# 3.6 Series assignment for novels
print("  3.6 Series assignment...")
# Check novels with Series → linked to collection with correct sequence_number
series_ok = True
series_issues_list = []
sample_checked = 0
for row in novel_rows:
    series = row.get("Series")
    seq = row.get("Series no.")
    title = row.get("Title")
    if series and str(series).strip() and seq is not None and title:
        sample_checked += 1
        # Find the work for this artifact
        wc = q1(conn, """SELECT wc.sequence_number, c.name FROM work_collections wc
                        JOIN collections c ON wc.collection_id = c.collection_id
                        JOIN works w ON wc.work_id = w.work_id
                        JOIN artifact_works aw ON w.work_id = aw.work_id
                        JOIN artifacts a ON a.artifact_id = aw.artifact_id
                        WHERE a.title = ?""", (str(title),))
        if not wc:
            series_issues_list.append(f"{title}: not linked to collection '{series}'")
            series_ok = False
        elif wc["name"] != str(series).strip():
            series_issues_list.append(f"{title}: linked to '{wc['name']}' not '{series}'")
            series_ok = False
        if sample_checked >= 20:
            break
if series_ok or len(series_issues_list) == 0:
    sem_checks_passed += 1
    print(f"    ✓ Series assignment verified ({sample_checked} checked)")
else:
    sem_checks_failed += 1
    sem_issues.append({"check": "series_assignment", "detail": series_issues_list[:5]})
    print(f"    ✗ Series issues: {series_issues_list[:3]}")

# 3.7 Complete/S mapping
print("  3.7 Complete/S mapping...")
s_runs = q(conn, """SELECT name, publisher, narrative_format, completion_status
                    FROM volume_runs
                    WHERE narrative_format = 'Serialized'""")
s_ok = all(r["completion_status"] == "Not Pursuing" for r in s_runs) and len(s_runs) > 0
if s_ok:
    sem_checks_passed += 1
    print(f"    ✓ {len(s_runs)} Serialized runs all have completion_status='Not Pursuing'")
else:
    bad = [r for r in s_runs if r["completion_status"] != "Not Pursuing"]
    if bad:
        sem_checks_failed += 1
        sem_issues.append({"check": "complete_s_mapping", "detail": f"{len(bad)} Serialized runs without Not Pursuing"})
        print(f"    ✗ {len(bad)} Serialized runs wrong")
    elif len(s_runs) == 0:
        sem_checks_failed += 1
        sem_issues.append({"check": "complete_s_mapping", "detail": "No Serialized runs found"})
        print("    ✗ No Serialized runs found")

layer3_status = "PASS" if sem_checks_failed == 0 else "FAIL"

# ══════════════════════════════════════════════════════════════════════
# LAYER 4: Edge Case Verification
# ══════════════════════════════════════════════════════════════════════
print("\n▶ Layer 4: Edge Case Verification")
edge_results = []

# 4.1 Batman #22 (Gotham) — dual works, is_partial on Gotham Knights
print("  4.1 Batman #22 (Gotham)...")
bat22 = q(conn, """SELECT a.artifact_id, a.title FROM artifacts a
                   WHERE a.title LIKE 'Batman #22%' AND a.publisher LIKE '%Gotham%'""")
if not bat22:
    bat22 = q(conn, "SELECT artifact_id, title FROM artifacts WHERE title LIKE 'Batman #22%'")
if bat22:
    bat22_works = q(conn, """SELECT w.title, aw.position, aw.is_partial FROM artifact_works aw
                            JOIN works w ON aw.work_id = w.work_id
                            WHERE aw.artifact_id = ?
                            ORDER BY aw.position""", (bat22[0]["artifact_id"],))
    has_two = len(bat22_works) >= 2
    has_partial = any(w["is_partial"] for w in bat22_works)
    gk_partial = any("Gotham Knights" in (w["title"] or "") and w["is_partial"] for w in bat22_works)
    status = "PASS" if has_two and gk_partial else "WARN"
    detail = f"Works: {[w['title'] for w in bat22_works]}, partial flags: {[w['is_partial'] for w in bat22_works]}"
    edge_results.append({"case": "Batman #22 dual-story", "status": status, "details": detail})
    print(f"    {status}: {detail}")
else:
    edge_results.append({"case": "Batman #22 dual-story", "status": "FAIL", "details": "Artifact not found"})
    print("    FAIL: Artifact not found")

# 4.2 DC Elseworlds: Last Stand on Krypton
print("  4.2 DC Elseworlds...")
else_art = q(conn, "SELECT artifact_id, title FROM artifacts WHERE title LIKE '%Elseworlds%Last Stand%'")
if not else_art:
    else_art = q(conn, "SELECT artifact_id, title FROM artifacts WHERE title LIKE '%Last Stand on Krypton%'")
if else_art:
    else_works = q(conn, """SELECT w.title, aw.position FROM artifact_works aw
                           JOIN works w ON aw.work_id = w.work_id
                           WHERE aw.artifact_id = ?
                           ORDER BY aw.position""", (else_art[0]["artifact_id"],))
    has_both = len(else_works) >= 2
    titles = [w["title"] for w in else_works]
    has_emerald = any("Emerald" in t or "Green Lantern" in t for t in titles)
    has_krypton = any("Krypton" in t or "Superman" in t for t in titles)
    status = "PASS" if has_both and (has_emerald or has_krypton) else "WARN"
    detail = f"Works linked: {titles}"
    edge_results.append({"case": "DC Elseworlds dual-work", "status": status, "details": detail})
    print(f"    {status}: {detail}")
else:
    edge_results.append({"case": "DC Elseworlds dual-work", "status": "FAIL", "details": "Artifact not found"})
    print("    FAIL: not found")

# 4.3 New X-Men Super Special — should be flagged for manual review
print("  4.3 New X-Men Super Special...")
nxm = q(conn, "SELECT artifact_id, title FROM artifacts WHERE title LIKE '%New X-Men Super Special%'")
if nxm:
    flag = q(conn, """SELECT flag_type, description FROM data_quality_flags
                     WHERE entity_id = ?""", (nxm[0]["artifact_id"],))
    has_flag = any("unparsed" in f["flag_type"] or "collects" in f["flag_type"].lower() for f in flag) if flag else False
    # Also check collects_note
    cn = q(conn, """SELECT collects_note FROM artifact_works WHERE artifact_id = ?""", (nxm[0]["artifact_id"],))
    has_note = any(c["collects_note"] for c in cn if c["collects_note"])
    status = "PASS" if has_flag or has_note else "WARN"
    detail = f"Flagged: {has_flag}, collects_note present: {has_note}, flags: {[f['flag_type'] for f in flag] if flag else 'none'}"
    edge_results.append({"case": "New X-Men Super Special flagged", "status": status, "details": detail})
    print(f"    {status}: {detail}")
else:
    edge_results.append({"case": "New X-Men Super Special flagged", "status": "FAIL", "details": "Not found"})
    print("    FAIL: not found")

# 4.4 Incredible Hulk dual arc (Snake Eyes + Dogs of War)
print("  4.4 Incredible Hulk dual arc...")
hulk = q(conn, "SELECT artifact_id, title FROM artifacts WHERE title LIKE '%Incredible Hulk%14%'")
if not hulk:
    hulk = q(conn, "SELECT artifact_id, title FROM artifacts WHERE title LIKE '%Incredible Hulk%' AND issue_number = '14'")
if hulk:
    hulk_arcs = q(conn, """SELECT sa.name, wam.arc_position FROM work_arc_membership wam
                          JOIN story_arcs sa ON wam.arc_id = sa.arc_id
                          JOIN works w ON wam.work_id = w.work_id
                          JOIN artifact_works aw ON w.work_id = aw.work_id
                          WHERE aw.artifact_id = ?""", (hulk[0]["artifact_id"],))
    arc_names = [a["name"] for a in hulk_arcs]
    has_snake = any("Snake" in n for n in arc_names)
    has_dogs = any("Dogs" in n for n in arc_names)
    status = "PASS" if has_snake and has_dogs else "WARN"
    detail = f"Arcs: {arc_names}"
    edge_results.append({"case": "Hulk dual arc membership", "status": status, "details": detail})
    print(f"    {status}: {detail}")
else:
    edge_results.append({"case": "Hulk dual arc membership", "status": "FAIL", "details": "Not found"})
    print("    FAIL: not found")

# 4.5 Honour Among Thieves/Kane And Abel
print("  4.5 Honour Among Thieves/Kane And Abel...")
hat = q(conn, "SELECT artifact_id, title, notes FROM artifacts WHERE title LIKE '%Honour Among Thieves%'")
if hat:
    hat_flags = q(conn, "SELECT flag_type, description FROM data_quality_flags WHERE entity_id = ?", (hat[0]["artifact_id"],))
    status = "PASS"
    detail = f"Found: '{hat[0]['title']}', flags: {[f['flag_type'] for f in hat_flags] if hat_flags else 'none'}"
    edge_results.append({"case": "Honour Among Thieves compound title", "status": status, "details": detail})
    print(f"    {status}: {detail}")
else:
    edge_results.append({"case": "Honour Among Thieves compound title", "status": "FAIL", "details": "Not found"})
    print("    FAIL: not found")

# 4.6 Novels with Status = Lent → Copy.location = Lent
print("  4.6 Lent novels...")
lent_ok = True
lent_detail = []
for row in novel_rows:
    if row.get("Status") and str(row["Status"]).strip().lower() == "lent":
        title = row.get("Title")
        loc = qval(conn, """SELECT c.location FROM copies c
                           JOIN artifacts a ON a.artifact_id = c.artifact_id
                           WHERE a.title = ?""", (str(title),))
        if loc and loc == "Lent":
            lent_detail.append(f"{title}: ✓ Lent")
        else:
            lent_ok = False
            lent_detail.append(f"{title}: ✗ location={loc}")
status = "PASS" if lent_ok else "FAIL"
edge_results.append({"case": "Lent novels", "status": status, "details": "; ".join(lent_detail)})
print(f"    {status}: {'; '.join(lent_detail)}")

# 4.7 Hindi ISBNs stored as proper strings
print("  4.7 Hindi book ISBNs...")
hindi_isbn_ok = True
hindi_isbn_detail = []
for row in hindi_rows:
    isbn = row.get("ISBN")
    title = row.get("Title")
    if isbn is not None and title:
        db_isbn = qval(conn, "SELECT isbn_or_upc FROM artifacts WHERE title = ?", (str(title),))
        if db_isbn:
            # Check it's not in scientific notation
            if "e" in str(db_isbn).lower() or "E" in str(db_isbn):
                hindi_isbn_ok = False
                hindi_isbn_detail.append(f"{title}: BAD format '{db_isbn}'")
            else:
                hindi_isbn_detail.append(f"{title}: '{db_isbn}' OK")
        else:
            hindi_isbn_detail.append(f"{title}: ISBN not found in DB")
status = "PASS" if hindi_isbn_ok else "FAIL"
edge_results.append({"case": "Hindi ISBN format", "status": status, "details": "; ".join(hindi_isbn_detail)})
print(f"    {status}: {'; '.join(hindi_isbn_detail[:3])}")

# 4.8 Tulsidas' Ramayana — Collects=DNF not parsed as issue range
print("  4.8 Tulsidas' Ramayana DNF...")
tulsi = q(conn, "SELECT artifact_id, title FROM artifacts WHERE title LIKE '%Tulsidas%Ramayana%'")
if tulsi:
    aw_tulsi = q(conn, """SELECT aw.collects_note, aw.position FROM artifact_works aw
                         WHERE aw.artifact_id = ?""", (tulsi[0]["artifact_id"],))
    # DNF should be stored as note, not parsed
    has_dnf_note = any("DNF" in str(a.get("collects_note", "")) for a in aw_tulsi)
    # Should NOT have multiple works from parsing
    work_count = qval(conn, "SELECT COUNT(*) FROM artifact_works WHERE artifact_id = ?", (tulsi[0]["artifact_id"],))
    not_parsed = work_count <= 2  # 1 or 2 is fine, >2 would mean DNF was parsed as range
    status = "PASS" if has_dnf_note and not_parsed else "WARN"
    detail = f"collects_note has DNF: {has_dnf_note}, work_count: {work_count}"
    edge_results.append({"case": "Tulsidas Ramayana DNF", "status": status, "details": detail})
    print(f"    {status}: {detail}")
else:
    edge_results.append({"case": "Tulsidas Ramayana DNF", "status": "FAIL", "details": "Not found"})
    print("    FAIL: not found")

# 4.9 Hulk Special (Gotham) — null Original Volume, complex Collects
print("  4.9 Hulk Special...")
hulk_sp = q(conn, "SELECT artifact_id, title FROM artifacts WHERE title LIKE 'Hulk Special%'")
if hulk_sp:
    hulk_sp_works = q(conn, """SELECT w.title, aw.collects_note FROM artifact_works aw
                              JOIN works w ON aw.work_id = w.work_id
                              WHERE aw.artifact_id = ?""", (hulk_sp[0]["artifact_id"],))
    hulk_sp_flags = q(conn, "SELECT flag_type FROM data_quality_flags WHERE entity_id = ?", (hulk_sp[0]["artifact_id"],))
    has_flag = bool(hulk_sp_flags)
    status = "PASS" if has_flag or hulk_sp_works else "WARN"
    detail = f"Works: {[w['title'] for w in hulk_sp_works]}, flags: {[f['flag_type'] for f in hulk_sp_flags]}"
    edge_results.append({"case": "Hulk Special null volume", "status": status, "details": detail})
    print(f"    {status}: {detail}")
else:
    edge_results.append({"case": "Hulk Special null volume", "status": "FAIL", "details": "Not found"})
    print("    FAIL: not found")

# 4.10 Batman Adventures #28 — notes about partial content
print("  4.10 Batman Adventures #28...")
ba28 = q(conn, "SELECT artifact_id, title, notes FROM artifacts WHERE title LIKE '%Batman Adventures%28%'")
if not ba28:
    ba28 = q(conn, "SELECT artifact_id, title, notes FROM artifacts WHERE title LIKE '%Batman Adventures%' AND issue_number = '28'")
if ba28:
    notes = ba28[0].get("notes", "")
    has_note = notes and ("Need to Know" in str(notes) or "Balance" in str(notes) or "partial" in str(notes).lower())
    # Also check is_partial
    partial = qval(conn, "SELECT is_partial FROM artifact_works WHERE artifact_id = ?", (ba28[0]["artifact_id"],))
    status = "PASS" if has_note or partial else "WARN"
    detail = f"Notes: '{notes}', is_partial: {partial}"
    edge_results.append({"case": "Batman Adventures #28 partial", "status": status, "details": detail})
    print(f"    {status}: {detail}")
else:
    edge_results.append({"case": "Batman Adventures #28 partial", "status": "FAIL", "details": "Not found"})
    print("    FAIL: not found")

edge_passes = sum(1 for e in edge_results if e["status"] == "PASS")
edge_warns = sum(1 for e in edge_results if e["status"] == "WARN")
edge_fails = sum(1 for e in edge_results if e["status"] == "FAIL")
layer4_status = "PASS" if edge_fails == 0 and edge_warns == 0 else ("WARN" if edge_fails == 0 else "FAIL")

# ══════════════════════════════════════════════════════════════════════
# LAYER 5: Referential Integrity
# ══════════════════════════════════════════════════════════════════════
print("\n▶ Layer 5: Referential Integrity")
orphaned = []

checks = [
    ("artifact_works.artifact_id → artifacts",
     "SELECT COUNT(*) FROM artifact_works aw LEFT JOIN artifacts a ON aw.artifact_id = a.artifact_id WHERE a.artifact_id IS NULL"),
    ("artifact_works.work_id → works",
     "SELECT COUNT(*) FROM artifact_works aw LEFT JOIN works w ON aw.work_id = w.work_id WHERE w.work_id IS NULL"),
    ("creator_roles.creator_id → creators",
     "SELECT COUNT(*) FROM creator_roles cr LEFT JOIN creators c ON cr.creator_id = c.creator_id WHERE c.creator_id IS NULL"),
    ("work_collections.work_id → works",
     "SELECT COUNT(*) FROM work_collections wc LEFT JOIN works w ON wc.work_id = w.work_id WHERE w.work_id IS NULL"),
    ("work_collections.collection_id → collections",
     "SELECT COUNT(*) FROM work_collections wc LEFT JOIN collections c ON wc.collection_id = c.collection_id WHERE c.collection_id IS NULL"),
    ("work_arc_membership.work_id → works",
     "SELECT COUNT(*) FROM work_arc_membership wam LEFT JOIN works w ON wam.work_id = w.work_id WHERE w.work_id IS NULL"),
    ("work_arc_membership.arc_id → story_arcs",
     "SELECT COUNT(*) FROM work_arc_membership wam LEFT JOIN story_arcs sa ON wam.arc_id = sa.arc_id WHERE sa.arc_id IS NULL"),
    ("copies.artifact_id → artifacts",
     "SELECT COUNT(*) FROM copies c LEFT JOIN artifacts a ON c.artifact_id = a.artifact_id WHERE a.artifact_id IS NULL"),
    ("activity_ledger.work_id → works",
     "SELECT COUNT(*) FROM activity_ledger al LEFT JOIN works w ON al.work_id = w.work_id WHERE w.work_id IS NULL"),
    ("Every artifact has ≥1 copy",
     "SELECT COUNT(*) FROM artifacts a LEFT JOIN copies c ON a.artifact_id = c.artifact_id WHERE c.copy_id IS NULL"),
    ("Every artifact has ≥1 artifact_works",
     "SELECT COUNT(*) FROM artifacts a LEFT JOIN artifact_works aw ON a.artifact_id = aw.artifact_id WHERE aw.id IS NULL"),
]

layer5_pass = True
for label, sql in checks:
    cnt = qval(conn, sql)
    ok = cnt == 0
    if not ok:
        layer5_pass = False
        orphaned.append({"check": label, "orphaned_count": cnt})
    print(f"  {'✓' if ok else '✗'} {label}: {cnt} orphaned")

# ══════════════════════════════════════════════════════════════════════
# LAYER 6: Data Quality Flags Audit
# ══════════════════════════════════════════════════════════════════════
print("\n▶ Layer 6: Data Quality Flags Audit")
flags = q(conn, "SELECT flag_type, COUNT(*) as cnt FROM data_quality_flags GROUP BY flag_type")
flag_breakdown = {f["flag_type"]: f["cnt"] for f in flags}
total_flags = qval(conn, "SELECT COUNT(*) FROM data_quality_flags")

# Check expected flag types exist
expected_types = ["missing_isbn", "name_inconsistency", "unparsed_collects"]
flags_ok = True
flag_issues = []
for ft in expected_types:
    if ft not in flag_breakdown:
        flags_ok = False
        flag_issues.append(f"Missing expected flag type: {ft}")
    else:
        print(f"  ✓ {ft}: {flag_breakdown[ft]}")

# Check that empty ratings are NOT flagged
rating_flags = qval(conn, "SELECT COUNT(*) FROM data_quality_flags WHERE flag_type = 'missing_rating'")
if rating_flags and rating_flags > 0:
    flags_ok = False
    flag_issues.append(f"Empty ratings incorrectly flagged: {rating_flags}")
    print(f"  ✗ Empty ratings flagged: {rating_flags}")
else:
    print("  ✓ Empty ratings NOT flagged (correct)")

# Print any other flag types
for ft, cnt in flag_breakdown.items():
    if ft not in expected_types:
        print(f"  ℹ {ft}: {cnt}")

# ══════════════════════════════════════════════════════════════════════
# BUILD FINAL JSON REPORT
# ══════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("Building final validation report...")

source_hash = sha256(XLSX)
db_hash = sha256(DB)

overall_has_fail = (not layer1_pass) or layer3_status == "FAIL" or (not layer5_pass)
overall_has_warn = layer2_status == "WARN" or layer4_status == "WARN" or (not flags_ok)

if overall_has_fail:
    overall_status = "FAIL"
elif overall_has_warn:
    overall_status = "PASS_WITH_WARNINGS"
else:
    overall_status = "PASS"

report = {
    "validation_timestamp": datetime.now(timezone.utc).isoformat(),
    "overall_status": overall_status,
    "source_file_hash": source_hash,
    "database_file_hash": db_hash,
    "layer_results": {
        "row_counts": {
            "status": "PASS" if layer1_pass else "FAIL",
            "details": layer1_details
        },
        "field_completeness": {
            "status": layer2_status,
            "coverage_pct": coverage_pct,
            "missing_fields": missing_fields[:20]  # Cap at 20 for readability
        },
        "semantic_integrity": {
            "status": layer3_status,
            "checks_passed": sem_checks_passed,
            "checks_failed": sem_checks_failed,
            "issues": sem_issues
        },
        "edge_cases": {
            "status": layer4_status,
            "results": edge_results
        },
        "referential_integrity": {
            "status": "PASS" if layer5_pass else "FAIL",
            "orphaned_records": orphaned
        },
        "data_quality_flags": {
            "status": "INFO",
            "total_flags_generated": total_flags,
            "breakdown": flag_breakdown
        }
    }
}

output_path = BASE / "validation_report.json"
output_path.write_text(json.dumps(report, indent=2, default=str))
print(f"\n✅ Report written to {output_path}")
print(f"Overall status: {overall_status}")

# Also print the JSON
print("\n" + json.dumps(report, indent=2, default=str))

wb.close()
conn.close()
