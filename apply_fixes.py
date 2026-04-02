#!/usr/bin/env python3
"""Apply approved fixes to utskomia.db based on flag review."""

import sqlite3
import uuid
from datetime import datetime, timezone

DB = "utskomia.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
now = datetime.now(timezone.utc).isoformat()

def new_id():
    return str(uuid.uuid4())

def execute(sql, params=()):
    conn.execute(sql, params)

def query(sql, params=()):
    return conn.execute(sql, params).fetchall()

def query_one(sql, params=()):
    rows = conn.execute(sql, params).fetchall()
    return rows[0] if rows else None

# ══════════════════════════════════════════════════════════════════════
# 1. DISMISS FLAGS
# ══════════════════════════════════════════════════════════════════════
print("▶ Dismissing flags...")

# Dismiss all 36 missing_isbn flags
r = conn.execute("UPDATE data_quality_flags SET status='dismissed', resolved_at=? WHERE flag_type='missing_isbn'", (now,))
print(f"  Dismissed {r.rowcount} missing_isbn flags")

# Dismiss all 24 conflicting_data flags
r = conn.execute("UPDATE data_quality_flags SET status='dismissed', resolved_at=? WHERE flag_type='conflicting_data'", (now,))
print(f"  Dismissed {r.rowcount} conflicting_data flags")

# Dismiss 80 false-positive name_inconsistency flags (all except the 4 genuine ones)
# The 4 genuine pairs: Greg/Gregg Rucka, Mike W/Mike W. Barr, Min S/Min S. Ku, Isaac/Issac Asimov
genuine_names = ["Gregg Rucka", "Mike W Barr", "Min S Ku", "Issac Asimov"]
genuine_ids = []
for name in genuine_names:
    row = query_one("SELECT creator_id FROM creators WHERE display_name = ?", (name,))
    if row:
        genuine_ids.append(row["creator_id"])

# Dismiss all name_inconsistency flags NOT involving the genuine duplicates
if genuine_ids:
    placeholders = ",".join("?" * len(genuine_ids))
    r = conn.execute(
        f"UPDATE data_quality_flags SET status='dismissed', resolved_at=? WHERE flag_type='name_inconsistency' AND entity_id NOT IN ({placeholders})",
        (now, *genuine_ids)
    )
    print(f"  Dismissed {r.rowcount} false-positive name_inconsistency flags")
else:
    r = conn.execute("UPDATE data_quality_flags SET status='dismissed', resolved_at=? WHERE flag_type='name_inconsistency'", (now,))
    print(f"  Dismissed {r.rowcount} name_inconsistency flags (couldn't find genuine dupes)")

# Dismiss Calvin & Hobbes unparsed_collects flag
calvin = query_one("SELECT artifact_id FROM artifacts WHERE title LIKE '%Calvin%Hobbes%Shadow%Night%'")
if calvin:
    r = conn.execute("UPDATE data_quality_flags SET status='dismissed', resolved_at=? WHERE entity_id=? AND flag_type='unparsed_collects'", (now, calvin["artifact_id"]))
    print(f"  Dismissed Calvin & Hobbes unparsed_collects flag ({r.rowcount})")

# ══════════════════════════════════════════════════════════════════════
# 2. MERGE 4 DUPLICATE CREATOR PAIRS
# ══════════════════════════════════════════════════════════════════════
print("\n▶ Merging duplicate creators...")

merge_pairs = [
    ("Gregg Rucka", "Greg Rucka"),       # keep Greg Rucka
    ("Mike W Barr", "Mike W. Barr"),     # keep Mike W. Barr
    ("Min S Ku", "Min S. Ku"),           # keep Min S. Ku
    ("Issac Asimov", "Isaac Asimov"),    # keep Isaac Asimov
]

for bad_name, good_name in merge_pairs:
    bad = query_one("SELECT creator_id FROM creators WHERE display_name = ?", (bad_name,))
    good = query_one("SELECT creator_id FROM creators WHERE display_name = ?", (good_name,))
    if bad and good:
        bad_id = bad["creator_id"]
        good_id = good["creator_id"]
        # Reassign all creator_roles from bad to good
        r = conn.execute("UPDATE creator_roles SET creator_id = ? WHERE creator_id = ?", (good_id, bad_id))
        print(f"  Merged '{bad_name}' → '{good_name}': reassigned {r.rowcount} roles")
        # Delete the bad creator
        conn.execute("DELETE FROM creators WHERE creator_id = ?", (bad_id,))
        # Resolve the flag
        conn.execute("UPDATE data_quality_flags SET status='resolved', resolved_at=? WHERE entity_id=?", (now, bad_id))
    else:
        print(f"  ⚠ Could not find pair: '{bad_name}' / '{good_name}'")

# ══════════════════════════════════════════════════════════════════════
# 3. PARSE UNPARSED COLLECTS → CREATE WORKS
# ══════════════════════════════════════════════════════════════════════
print("\n▶ Creating Works from unparsed Collects...")

def find_or_create_volume_run(name, publisher):
    """Find an existing volume run or create a new one."""
    row = query_one("SELECT volume_run_id FROM volume_runs WHERE name = ? AND publisher = ?", (name, publisher))
    if row:
        return row["volume_run_id"]
    vr_id = new_id()
    execute("INSERT INTO volume_runs (volume_run_id, name, publisher, created_at, updated_at) VALUES (?,?,?,?,?)",
            (vr_id, name, publisher, now, now))
    return vr_id

def create_work(title, work_type="Comic Story", volume_run_id=None, issue_number=None, year=None):
    """Create a Work record."""
    # Check if an identical work already exists (avoid duplicates)
    if volume_run_id and issue_number:
        existing = query_one("SELECT work_id FROM works WHERE volume_run_id = ? AND issue_number = ?",
                           (volume_run_id, str(issue_number)))
        if existing:
            return existing["work_id"], False  # already exists

    wid = new_id()
    execute("""INSERT INTO works (work_id, title, work_type, volume_run_id, issue_number,
               original_publication_year, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (wid, title, work_type, volume_run_id, str(issue_number) if issue_number else None, year, now, now))
    return wid, True  # newly created

def link_work_to_artifact(artifact_id, work_id, position, is_partial=False, collects_note=None):
    """Link a work to an artifact via artifact_works."""
    # Check if link already exists
    existing = query_one("SELECT id FROM artifact_works WHERE artifact_id = ? AND work_id = ?",
                        (artifact_id, work_id))
    if existing:
        return False
    execute("""INSERT INTO artifact_works (id, artifact_id, work_id, position, is_partial, collects_note)
               VALUES (?,?,?,?,?,?)""",
            (new_id(), artifact_id, work_id, position, is_partial, collects_note))
    return True

def get_artifact(title_pattern):
    """Find artifact by title pattern."""
    row = query_one("SELECT artifact_id, title FROM artifacts WHERE title LIKE ?", (f"%{title_pattern}%",))
    return row

def get_current_max_position(artifact_id):
    """Get current max position for an artifact."""
    row = query_one("SELECT MAX(position) as mp FROM artifact_works WHERE artifact_id = ?", (artifact_id,))
    return row["mp"] if row and row["mp"] else 0

def resolve_unparsed_flag(artifact_id):
    """Mark the unparsed_collects flag as resolved."""
    conn.execute("UPDATE data_quality_flags SET status='resolved', resolved_at=? WHERE entity_id=? AND flag_type='unparsed_collects'",
                (now, artifact_id))

# --- Entry 1: Batman: Haunted Knight ---
print("  1. Batman: Haunted Knight → 3 LOTDK Halloween Specials")
art = get_artifact("Batman: Haunted Knight")
if art:
    aid = art["artifact_id"]
    # Remove the existing single Work link (generic)
    existing_works = query("SELECT aw.id, aw.work_id FROM artifact_works aw WHERE aw.artifact_id = ?", (aid,))

    vr_id = find_or_create_volume_run("Legends of the Dark Knight", "DC Comics")
    for i, year in enumerate([1993, 1994, 1995], 1):
        title = f"Legends of the Dark Knight Halloween Special {year}"
        wid, created = create_work(title, volume_run_id=vr_id, issue_number=f"Halloween Special {year}", year=year)
        link_work_to_artifact(aid, wid, i)
        print(f"    {'Created' if created else 'Linked existing'}: {title} @ pos {i}")
    resolve_unparsed_flag(aid)

# --- Entry 2: Bone: The Great Cow Race ---
print("  2. Bone: The Great Cow Race → 6 issues")
art = get_artifact("Bone: The Great Cow Race")
if art:
    aid = art["artifact_id"]
    vr_id = find_or_create_volume_run("Bone", "Cartoon Books")
    issues = [7, 8, 9, 10, 11, "13.5"]
    for i, iss in enumerate(issues, 1):
        title = f"Bone #{iss}"
        wid, created = create_work(title, volume_run_id=vr_id, issue_number=str(iss))
        link_work_to_artifact(aid, wid, i)
        print(f"    {'Created' if created else 'Linked existing'}: {title} @ pos {i}")
    resolve_unparsed_flag(aid)

# --- Entry 3: Calvin & Hobbes — already dismissed above ---

# --- Entry 4: DC Elseworlds: Last Stand on Krypton ---
print("  4. DC Elseworlds → 2 Works (Green Lantern + Superman)")
art = get_artifact("DC Elseworlds: Last Stand on Krypton")
if art:
    aid = art["artifact_id"]
    # Remove the existing generic work link
    old_aw = query("SELECT aw.id, aw.work_id, w.title FROM artifact_works aw JOIN works w ON aw.work_id = w.work_id WHERE aw.artifact_id = ?", (aid,))

    # Create Green Lantern: 1001 Emerald Nights
    gl_vr = find_or_create_volume_run("Green Lantern: 1001 Emerald Nights", "DC Comics")
    gl_wid, gl_created = create_work("Green Lantern: 1001 Emerald Nights", volume_run_id=gl_vr, issue_number="1", year=2001)

    # Create Superman: Last Stand on Krypton
    sm_vr = find_or_create_volume_run("Superman: Last Stand on Krypton", "DC Comics")
    sm_wid, sm_created = create_work("Superman: Last Stand on Krypton", volume_run_id=sm_vr, issue_number="1", year=2003)

    # Link creators to the works
    # Writer: LaBan, Terry → GL; Gerber, Steve → Superman
    terry = query_one("SELECT creator_id FROM creators WHERE display_name = 'Terry LaBan'")
    steve_g = query_one("SELECT creator_id FROM creators WHERE display_name = 'Steve Gerber'")
    rebecca = query_one("SELECT creator_id FROM creators WHERE display_name = 'Rebecca Guay'")
    doug_w = query_one("SELECT creator_id FROM creators WHERE display_name = 'Doug Wheatley'")

    if terry:
        execute("INSERT INTO creator_roles (id, creator_id, target_type, target_id, role) VALUES (?,?,?,?,?)",
                (new_id(), terry["creator_id"], "work", gl_wid, "Writer"))
    if rebecca:
        execute("INSERT INTO creator_roles (id, creator_id, target_type, target_id, role) VALUES (?,?,?,?,?)",
                (new_id(), rebecca["creator_id"], "work", gl_wid, "Artist"))
    if steve_g:
        execute("INSERT INTO creator_roles (id, creator_id, target_type, target_id, role) VALUES (?,?,?,?,?)",
                (new_id(), steve_g["creator_id"], "work", sm_wid, "Writer"))
    if doug_w:
        execute("INSERT INTO creator_roles (id, creator_id, target_type, target_id, role) VALUES (?,?,?,?,?)",
                (new_id(), doug_w["creator_id"], "work", sm_wid, "Artist"))

    # Remove old generic work link and add new ones
    if old_aw:
        for aw in old_aw:
            execute("DELETE FROM artifact_works WHERE id = ?", (aw["id"],))
            # Also delete the old generic work if it has no other links
            other_links = query_one("SELECT COUNT(*) as cnt FROM artifact_works WHERE work_id = ?", (aw["work_id"],))
            if other_links and other_links["cnt"] == 0:
                # Delete old creator_roles pointing to this work
                execute("DELETE FROM creator_roles WHERE target_id = ?", (aw["work_id"],))
                execute("DELETE FROM works WHERE work_id = ?", (aw["work_id"],))
                print(f"    Removed old generic work: {aw['title']}")

    link_work_to_artifact(aid, gl_wid, 1)
    link_work_to_artifact(aid, sm_wid, 2)
    print(f"    {'Created' if gl_created else 'Linked'}: Green Lantern: 1001 Emerald Nights @ pos 1")
    print(f"    {'Created' if sm_created else 'Linked'}: Superman: Last Stand on Krypton @ pos 2")
    resolve_unparsed_flag(aid)

# --- Entry 5: Fantastic Four - Super Special ---
print("  5. Fantastic Four Super Special → 6 Works")
art = get_artifact("Fantastic Four - Super Special")
if art:
    aid = art["artifact_id"]
    vr_id = find_or_create_volume_run("Fantastic Four", "Marvel")
    for i, iss in enumerate(range(35, 40), 1):
        title = f"Fantastic Four (Vol 3) #{iss}"
        wid, created = create_work(title, volume_run_id=vr_id, issue_number=str(iss))
        link_work_to_artifact(aid, wid, i)
        print(f"    {'Created' if created else 'Linked existing'}: {title} @ pos {i}")
    # Annual '98
    ann_wid, ann_created = create_work("Fantastic Four Annual 1998", volume_run_id=vr_id, issue_number="Annual 1998", year=1998)
    link_work_to_artifact(aid, ann_wid, 6)
    print(f"    {'Created' if ann_created else 'Linked existing'}: Fantastic Four Annual 1998 @ pos 6")
    resolve_unparsed_flag(aid)

# --- Entry 6: Hulk Special ---
print("  6. Hulk Special → 5 Works")
art = get_artifact("Hulk Special")
if art:
    aid = art["artifact_id"]
    # Remove old generic work
    old_aw = query("SELECT aw.id, aw.work_id, w.title FROM artifact_works aw JOIN works w ON aw.work_id = w.work_id WHERE aw.artifact_id = ?", (aid,))
    if old_aw:
        for aw in old_aw:
            execute("DELETE FROM artifact_works WHERE id = ?", (aw["id"],))
            other = query_one("SELECT COUNT(*) as cnt FROM artifact_works WHERE work_id = ?", (aw["work_id"],))
            if other and other["cnt"] == 0:
                execute("DELETE FROM creator_roles WHERE target_id = ?", (aw["work_id"],))
                execute("DELETE FROM works WHERE work_id = ?", (aw["work_id"],))
                print(f"    Removed old generic work: {aw['title']}")

    hulk_vr = find_or_create_volume_run("The Incredible Hulk", "Marvel")
    umtu_vr = find_or_create_volume_run("Ultimate Marvel Team-Up", "Marvel")

    works_to_create = [
        ("Incredible Hulk (Vol 3) #34", hulk_vr, "34", False),
        ("Incredible Hulk (Vol 3) #35", hulk_vr, "35", False),
        ("Ultimate Marvel Team-Up #2", umtu_vr, "2", False),
        ("Incredible Hulk Annual 2001", hulk_vr, "Annual 2001", False),
        ("Incredible Hulk (Vol 3) #1", hulk_vr, "1", True),  # partial
    ]
    for i, (title, vr, iss, partial) in enumerate(works_to_create, 1):
        wid, created = create_work(title, volume_run_id=vr, issue_number=iss)
        link_work_to_artifact(aid, wid, i, is_partial=partial)
        label = " (partial)" if partial else ""
        print(f"    {'Created' if created else 'Linked existing'}: {title}{label} @ pos {i}")
    resolve_unparsed_flag(aid)

# --- Entry 7: JLA: League of One - Super Special ---
print("  7. JLA: League of One Super Special → 2 Works")
art = get_artifact("JLA: League of One - Super Special")
if art:
    aid = art["artifact_id"]
    old_aw = query("SELECT aw.id, aw.work_id, w.title FROM artifact_works aw JOIN works w ON aw.work_id = w.work_id WHERE aw.artifact_id = ?", (aid,))
    if old_aw:
        for aw in old_aw:
            execute("DELETE FROM artifact_works WHERE id = ?", (aw["id"],))
            other = query_one("SELECT COUNT(*) as cnt FROM artifact_works WHERE work_id = ?", (aw["work_id"],))
            if other and other["cnt"] == 0:
                execute("DELETE FROM creator_roles WHERE target_id = ?", (aw["work_id"],))
                execute("DELETE FROM works WHERE work_id = ?", (aw["work_id"],))

    jla_vr = find_or_create_volume_run("JLA: League of One", "DC Comics")
    bat_vr = find_or_create_volume_run("Batman: Reign of Terror", "DC Comics")

    w1, c1 = create_work("JLA: League of One", volume_run_id=jla_vr, issue_number="1", year=2000)
    w2, c2 = create_work("Batman: Reign of Terror", volume_run_id=bat_vr, issue_number="1", year=1999)
    link_work_to_artifact(aid, w1, 1)
    link_work_to_artifact(aid, w2, 2)
    print(f"    {'Created' if c1 else 'Linked'}: JLA: League of One @ pos 1")
    print(f"    {'Created' if c2 else 'Linked'}: Batman: Reign of Terror @ pos 2")
    resolve_unparsed_flag(aid)

# --- Entry 8: Joker ---
print("  8. Joker → 2 Works")
art = get_artifact("Joker")
# Be careful — "Joker" might match other things
art = query_one("SELECT artifact_id, title FROM artifacts WHERE title = 'Joker' AND format = 'Graphic Novel'")
if art:
    aid = art["artifact_id"]
    old_aw = query("SELECT aw.id, aw.work_id, w.title FROM artifact_works aw JOIN works w ON aw.work_id = w.work_id WHERE aw.artifact_id = ?", (aid,))
    if old_aw:
        for aw in old_aw:
            execute("DELETE FROM artifact_works WHERE id = ?", (aw["id"],))
            other = query_one("SELECT COUNT(*) as cnt FROM artifact_works WHERE work_id = ?", (aw["work_id"],))
            if other and other["cnt"] == 0:
                execute("DELETE FROM creator_roles WHERE target_id = ?", (aw["work_id"],))
                execute("DELETE FROM works WHERE work_id = ?", (aw["work_id"],))

    joker_vr = find_or_create_volume_run("Joker", "DC Comics")
    j80_vr = find_or_create_volume_run("The Joker 80th Anniversary 100-Page Super Spectacular", "DC Comics")

    w1, c1 = create_work("Joker", volume_run_id=joker_vr, issue_number="1", year=2008)
    w2, c2 = create_work("Who Fell into the Hornet's Nest", volume_run_id=j80_vr, issue_number="1", year=2019)
    link_work_to_artifact(aid, w1, 1)
    link_work_to_artifact(aid, w2, 2)
    print(f"    {'Created' if c1 else 'Linked'}: Joker @ pos 1")
    print(f"    {'Created' if c2 else 'Linked'}: Who Fell into the Hornet's Nest @ pos 2")
    resolve_unparsed_flag(aid)

# --- Entry 9: Superman Special ---
print("  9. Superman Special → 5 Works")
# There are 2 Superman Specials — find the one with Y2K collects
art = query_one("""SELECT a.artifact_id, dqf.description FROM data_quality_flags dqf
                   JOIN artifacts a ON dqf.entity_id = a.artifact_id
                   WHERE dqf.description LIKE '%Y2K%'""")
if art:
    aid = art["artifact_id"]
    old_aw = query("SELECT aw.id, aw.work_id, w.title FROM artifact_works aw JOIN works w ON aw.work_id = w.work_id WHERE aw.artifact_id = ?", (aid,))
    if old_aw:
        for aw in old_aw:
            execute("DELETE FROM artifact_works WHERE id = ?", (aw["id"],))
            other = query_one("SELECT COUNT(*) as cnt FROM artifact_works WHERE work_id = ?", (aw["work_id"],))
            if other and other["cnt"] == 0:
                execute("DELETE FROM creator_roles WHERE target_id = ?", (aw["work_id"],))
                execute("DELETE FROM works WHERE work_id = ?", (aw["work_id"],))

    y2k_vr = find_or_create_volume_run("Superman: Y2K", "DC Comics")
    sup_vr = find_or_create_volume_run("Superman", "DC Comics")
    aos_vr = find_or_create_volume_run("Adventures of Superman", "DC Comics")
    mos_vr = find_or_create_volume_run("Superman: The Man of Steel", "DC Comics")
    ac_vr = find_or_create_volume_run("Action Comics", "DC Comics")

    works_data = [
        ("Superman: Y2K", y2k_vr, "1", 1999),
        ("Superman #154", sup_vr, "154", None),
        ("Adventures of Superman #576", aos_vr, "576", None),
        ("Superman: The Man of Steel #98", mos_vr, "98", None),
        ("Action Comics #763", ac_vr, "763", None),
    ]
    for i, (title, vr, iss, year) in enumerate(works_data, 1):
        wid, created = create_work(title, volume_run_id=vr, issue_number=iss, year=year)
        link_work_to_artifact(aid, wid, i)
        print(f"    {'Created' if created else 'Linked existing'}: {title} @ pos {i}")
    resolve_unparsed_flag(aid)

# --- Entry 10: Superman: Peace on Earth & Batman: War on Crime ---
print("  10. Superman: Peace on Earth & Batman: War on Crime → 2 Works")
art = get_artifact("Superman: Peace on Earth & Batman: War on Crime")
if art:
    aid = art["artifact_id"]
    old_aw = query("SELECT aw.id, aw.work_id, w.title FROM artifact_works aw JOIN works w ON aw.work_id = w.work_id WHERE aw.artifact_id = ?", (aid,))
    if old_aw:
        for aw in old_aw:
            execute("DELETE FROM artifact_works WHERE id = ?", (aw["id"],))
            other = query_one("SELECT COUNT(*) as cnt FROM artifact_works WHERE work_id = ?", (aw["work_id"],))
            if other and other["cnt"] == 0:
                execute("DELETE FROM creator_roles WHERE target_id = ?", (aw["work_id"],))
                execute("DELETE FROM works WHERE work_id = ?", (aw["work_id"],))

    spe_vr = find_or_create_volume_run("Superman: Peace on Earth", "DC Comics")
    bwc_vr = find_or_create_volume_run("Batman: War on Crime", "DC Comics")

    w1, c1 = create_work("Superman: Peace on Earth", volume_run_id=spe_vr, issue_number="1", year=1998)
    w2, c2 = create_work("Batman: War on Crime", volume_run_id=bwc_vr, issue_number="1", year=1999)
    link_work_to_artifact(aid, w1, 1)
    link_work_to_artifact(aid, w2, 2)
    print(f"    {'Created' if c1 else 'Linked'}: Superman: Peace on Earth @ pos 1")
    print(f"    {'Created' if c2 else 'Linked'}: Batman: War on Crime @ pos 2")
    resolve_unparsed_flag(aid)

# --- Entry 11: The Incredible Hulk: The End - Super Special ---
print("  11. Incredible Hulk: The End Super Special → 4 Works")
art = get_artifact("Incredible Hulk: The End - Super Special")
if art:
    aid = art["artifact_id"]
    old_aw = query("SELECT aw.id, aw.work_id, w.title FROM artifact_works aw JOIN works w ON aw.work_id = w.work_id WHERE aw.artifact_id = ?", (aid,))
    if old_aw:
        for aw in old_aw:
            execute("DELETE FROM artifact_works WHERE id = ?", (aw["id"],))
            other = query_one("SELECT COUNT(*) as cnt FROM artifact_works WHERE work_id = ?", (aw["work_id"],))
            if other and other["cnt"] == 0:
                execute("DELETE FROM creator_roles WHERE target_id = ?", (aw["work_id"],))
                execute("DELETE FROM works WHERE work_id = ?", (aw["work_id"],))

    hulk_end_vr = find_or_create_volume_run("Hulk: The End", "Marvel")
    hulk_smash_vr = find_or_create_volume_run("Hulk Smash", "Marvel")
    ss_vr = find_or_create_volume_run("Startling Stories: The Thing", "Marvel")

    works_data = [
        ("Hulk: The End", hulk_end_vr, "1"),
        ("Hulk Smash #1", hulk_smash_vr, "1"),
        ("Hulk Smash #2", hulk_smash_vr, "2"),
        ("Startling Stories: The Thing #1", ss_vr, "1"),
    ]
    for i, (title, vr, iss) in enumerate(works_data, 1):
        wid, created = create_work(title, volume_run_id=vr, issue_number=iss)
        link_work_to_artifact(aid, wid, i)
        print(f"    {'Created' if created else 'Linked existing'}: {title} @ pos {i}")
    resolve_unparsed_flag(aid)

# --- Entry 12: X-Men: Ronin Super Special ---
print("  12. X-Men: Ronin Super Special → 6 Works")
art = get_artifact("X-Men: Ronin Super Special")
if art:
    aid = art["artifact_id"]
    old_aw = query("SELECT aw.id, aw.work_id, w.title FROM artifact_works aw JOIN works w ON aw.work_id = w.work_id WHERE aw.artifact_id = ?", (aid,))
    if old_aw:
        for aw in old_aw:
            execute("DELETE FROM artifact_works WHERE id = ?", (aw["id"],))
            other = query_one("SELECT COUNT(*) as cnt FROM artifact_works WHERE work_id = ?", (aw["work_id"],))
            if other and other["cnt"] == 0:
                execute("DELETE FROM creator_roles WHERE target_id = ?", (aw["work_id"],))
                execute("DELETE FROM works WHERE work_id = ?", (aw["work_id"],))

    xr_vr = find_or_create_volume_run("X-Men: Ronin", "Marvel")
    mm_vr = find_or_create_volume_run("Marvel Mangaverse: Avengers Assemble", "Marvel")

    for i in range(1, 6):
        title = f"X-Men: Ronin #{i}"
        wid, created = create_work(title, volume_run_id=xr_vr, issue_number=str(i))
        link_work_to_artifact(aid, wid, i)
        print(f"    {'Created' if created else 'Linked existing'}: {title} @ pos {i}")

    w6, c6 = create_work("Marvel Mangaverse: Avengers Assemble", volume_run_id=mm_vr, issue_number="1")
    link_work_to_artifact(aid, w6, 6)
    print(f"    {'Created' if c6 else 'Linked existing'}: Marvel Mangaverse: Avengers Assemble @ pos 6")
    resolve_unparsed_flag(aid)

# ══════════════════════════════════════════════════════════════════════
# 4. VERIFY & COMMIT
# ══════════════════════════════════════════════════════════════════════
print("\n▶ Verification...")

# Count remaining open flags
open_flags = query_one("SELECT COUNT(*) as cnt FROM data_quality_flags WHERE status = 'open'")
resolved_flags = query_one("SELECT COUNT(*) as cnt FROM data_quality_flags WHERE status = 'resolved'")
dismissed_flags = query_one("SELECT COUNT(*) as cnt FROM data_quality_flags WHERE status = 'dismissed'")

print(f"  Flags: {open_flags['cnt']} open, {resolved_flags['cnt']} resolved, {dismissed_flags['cnt']} dismissed")

# Check referential integrity
orphan_aw = query_one("SELECT COUNT(*) as cnt FROM artifact_works aw LEFT JOIN artifacts a ON aw.artifact_id = a.artifact_id WHERE a.artifact_id IS NULL")
orphan_aw2 = query_one("SELECT COUNT(*) as cnt FROM artifact_works aw LEFT JOIN works w ON aw.work_id = w.work_id WHERE w.work_id IS NULL")
no_copy = query_one("SELECT COUNT(*) as cnt FROM artifacts a LEFT JOIN copies c ON a.artifact_id = c.artifact_id WHERE c.copy_id IS NULL")
no_aw = query_one("SELECT COUNT(*) as cnt FROM artifacts a LEFT JOIN artifact_works aw ON a.artifact_id = aw.artifact_id WHERE aw.id IS NULL")

print(f"  Orphaned artifact_works→artifacts: {orphan_aw['cnt']}")
print(f"  Orphaned artifact_works→works: {orphan_aw2['cnt']}")
print(f"  Artifacts without copies: {no_copy['cnt']}")
print(f"  Artifacts without works: {no_aw['cnt']}")

creators_count = query_one("SELECT COUNT(*) as cnt FROM creators")
works_count = query_one("SELECT COUNT(*) as cnt FROM works")
print(f"  Total creators: {creators_count['cnt']}")
print(f"  Total works: {works_count['cnt']}")

conn.commit()
print("\n✅ All fixes committed successfully.")
conn.close()
