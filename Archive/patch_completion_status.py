#!/usr/bin/env python3
"""Patch DB: move completion_status from volume_runs to story_arcs per D-028."""

import sqlite3
from collections import defaultdict
from datetime import datetime, timezone

import openpyxl

DB = "utskomia.db"
XLSX = "Our Library-3.xlsx"
now = datetime.now(timezone.utc).isoformat()

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# ── Step 1: Add completion_status column to story_arcs ─────────────
print("▶ Step 1: ALTER TABLE story_arcs ADD COLUMN completion_status")
try:
    conn.execute("ALTER TABLE story_arcs ADD COLUMN completion_status TEXT")
    print("  Added column")
except Exception as e:
    if "duplicate column" in str(e).lower():
        print("  Column already exists, skipping")
    else:
        raise

# ── Step 2: Read xlsx to get per-issue Complete values ─────────────
print("\n▶ Step 2: Reading xlsx for per-issue Complete + Story Arc values")
wb = openpyxl.load_workbook(XLSX, data_only=True, read_only=True)
ws = wb["Comics (Issues)"]
rows = list(ws.iter_rows(values_only=True))
headers = [str(h).strip() if h else f"_col{i}" for i, h in enumerate(rows[0])]

vol_idx = headers.index("Volume")
num_idx = headers.index("#")
complete_idx = headers.index("Complete")
arc_idx = headers.index("Story Arc")
arc_num_idx = headers.index("Arc #")

# Collect: for each (arc_name, total_parts_hint) → list of Y/N values
# We need to match arcs in DB by name. total_parts is in the arc_name parenthetical.
arc_votes = defaultdict(list)  # arc_name → [Y, N, Y, ...]

for row in rows[1:]:
    vol = row[vol_idx]
    if not vol:
        continue
    complete = row[complete_idx]
    arc_raw = row[arc_idx]
    if not arc_raw or not complete:
        continue
    complete = str(complete).strip().upper()
    if complete not in ("Y", "N"):
        continue  # S is for volume_runs, not arcs

    # Parse arc names — could be comma-separated dual arcs
    # e.g. "Snake Eyes (2), The Dogs of War (7)"
    arc_str = str(arc_raw).strip()

    # Split on comma, but be careful with parenthetical contents
    # Strategy: split on ", " where followed by a capital letter (new arc name)
    import re
    # Split dual arcs: "Snake Eyes (2), The Dogs of War (7)"
    arc_parts = re.split(r',\s*(?=[A-Z])', arc_str)

    for part in arc_parts:
        part = part.strip()
        if not part:
            continue
        # Extract arc name and optional total_parts
        m = re.match(r'^(.+?)\s*\((\d+)\)\s*$', part)
        if m:
            arc_name = m.group(1).strip()
        else:
            arc_name = part.strip()
        arc_votes[arc_name].append(complete)

wb.close()

print(f"  Found {len(arc_votes)} unique arc names with Y/N votes")

# ── Step 3: Match arcs to DB and set completion_status ─────────────
print("\n▶ Step 3: Setting completion_status on story_arcs")

matched = 0
unmatched = []
for arc_name, votes in arc_votes.items():
    # Find in DB
    db_arc = conn.execute("SELECT arc_id, name FROM story_arcs WHERE name = ?", (arc_name,)).fetchone()
    if not db_arc:
        # Try case-insensitive
        db_arc = conn.execute("SELECT arc_id, name FROM story_arcs WHERE LOWER(name) = LOWER(?)", (arc_name,)).fetchone()
    if not db_arc:
        unmatched.append(arc_name)
        continue

    # Majority vote
    y_count = votes.count("Y")
    n_count = votes.count("N")
    status = "Complete" if y_count >= n_count else "Incomplete"

    conn.execute("UPDATE story_arcs SET completion_status = ?, updated_at = ? WHERE arc_id = ?",
                (status, now, db_arc["arc_id"]))
    matched += 1

print(f"  Matched and updated: {matched} arcs")
if unmatched:
    print(f"  Unmatched arc names ({len(unmatched)}): {unmatched[:10]}")

# ── Step 4: Clear volume_runs.completion_status for non-Serialized ─
print("\n▶ Step 4: Clearing volume_runs.completion_status for non-Serialized runs")

# Keep Not Pursuing only where narrative_format = Serialized
r = conn.execute("""UPDATE volume_runs SET completion_status = NULL, updated_at = ?
                    WHERE narrative_format IS NULL OR narrative_format != 'Serialized'""", (now,))
print(f"  Cleared completion_status on {r.rowcount} non-Serialized volume_runs")

# Verify Serialized runs still have Not Pursuing
serialized = conn.execute("""SELECT name, publisher, completion_status FROM volume_runs
                            WHERE narrative_format = 'Serialized'""").fetchall()
print(f"  Serialized runs kept intact: {len(serialized)}")
for s in serialized:
    print(f"    {s['name']} ({s['publisher']}): {s['completion_status']}")

# ── Step 5: Verify ─────────────────────────────────────────────────
print("\n▶ Verification")
arcs_with_status = conn.execute("SELECT COUNT(*) as cnt FROM story_arcs WHERE completion_status IS NOT NULL").fetchone()
arcs_complete = conn.execute("SELECT COUNT(*) as cnt FROM story_arcs WHERE completion_status = 'Complete'").fetchone()
arcs_incomplete = conn.execute("SELECT COUNT(*) as cnt FROM story_arcs WHERE completion_status = 'Incomplete'").fetchone()
arcs_null = conn.execute("SELECT COUNT(*) as cnt FROM story_arcs WHERE completion_status IS NULL").fetchone()
vr_with_status = conn.execute("SELECT COUNT(*) as cnt FROM volume_runs WHERE completion_status IS NOT NULL").fetchone()

print(f"  story_arcs: {arcs_complete['cnt']} Complete, {arcs_incomplete['cnt']} Incomplete, {arcs_null['cnt']} NULL")
print(f"  volume_runs with completion_status: {vr_with_status['cnt']} (should equal Serialized count)")

conn.commit()
print("\n✅ Patch committed successfully.")
conn.close()
