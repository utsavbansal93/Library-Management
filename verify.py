"""
Utskomia Library — Independent Verification Script

Reads Our Library-3.xlsx and utskomia.db independently, cross-checks
row counts, field integrity, FK integrity, and edge cases.

This script does NOT import or rely on the migration script code.

Usage:
    python3 verify.py
"""

import sqlite3
import sys

import pandas as pd

XLSX_PATH = "Our Library-3.xlsx"
DB_PATH = "utskomia.db"


class VerificationResult:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.details = []

    def ok(self, name: str, detail: str = ""):
        self.checks_passed += 1
        self.details.append(("PASS", name, detail))
        print(f"  [PASS] {name}" + (f" — {detail}" if detail else ""))

    def fail(self, name: str, detail: str):
        self.checks_failed += 1
        self.details.append(("FAIL", name, detail))
        print(f"  [FAIL] {name} — {detail}")

    def warn(self, name: str, detail: str):
        self.details.append(("WARN", name, detail))
        print(f"  [WARN] {name} — {detail}")

    @property
    def overall(self) -> str:
        if self.checks_failed > 0:
            return "FAIL"
        return "PASS"


def count_non_empty_rows(df: pd.DataFrame, key_col: str) -> int:
    """Count rows where the key column is non-null and non-empty."""
    return df[key_col].dropna().apply(lambda x: str(x).strip() != "").sum()


def main():
    print("Utskomia Library — Independent Verification")
    print("=" * 55)
    result = VerificationResult()

    # Load sources
    try:
        xlsx = pd.ExcelFile(XLSX_PATH)
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"FATAL: Cannot open files: {e}")
        sys.exit(1)

    # ===================================================================
    # LAYER 1: Row Count Verification
    # ===================================================================
    print("\n--- Layer 1: Row Count Verification ---")

    sheet_checks = [
        ("Novels, etc..", "Title", "Novels"),
        ("Hindi Books", "Title", "Hindi Books"),
        ("Non-fiction", "Title", "Non-fiction"),
        ("Magazines", "Magazine", "Magazines"),
        ("Comics (GNs)", "Title", "Comics (GNs)"),
        ("Comics (Issues)", "Volume", "Comics (Issues)"),
    ]

    for sheet_name, key_col, source_sheet_tag in sheet_checks:
        df = pd.read_excel(xlsx, sheet_name)
        expected = count_non_empty_rows(df, key_col)
        actual = conn.execute(
            "SELECT COUNT(*) FROM artifacts WHERE source_sheet = ?",
            (source_sheet_tag,)
        ).fetchone()[0]
        if expected == actual:
            result.ok(f"Row count: {sheet_name}", f"{expected} rows -> {actual} artifacts")
        else:
            result.fail(f"Row count: {sheet_name}", f"Expected {expected}, got {actual}")

    total_expected = sum(
        count_non_empty_rows(pd.read_excel(xlsx, s), k) for s, k, _ in sheet_checks
    )
    total_actual = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
    if total_expected == total_actual:
        result.ok("Total artifact count", f"{total_expected}")
    else:
        result.fail("Total artifact count", f"Expected {total_expected}, got {total_actual}")

    # ===================================================================
    # LAYER 2: FK Integrity
    # ===================================================================
    print("\n--- Layer 2: FK / Referential Integrity ---")

    fk_checks = [
        ("artifact_works.artifact_id -> artifacts",
         "SELECT COUNT(*) FROM artifact_works aw LEFT JOIN artifacts a ON aw.artifact_id = a.artifact_id WHERE a.artifact_id IS NULL"),
        ("artifact_works.work_id -> works",
         "SELECT COUNT(*) FROM artifact_works aw LEFT JOIN works w ON aw.work_id = w.work_id WHERE w.work_id IS NULL"),
        ("work_collections.work_id -> works",
         "SELECT COUNT(*) FROM work_collections wc LEFT JOIN works w ON wc.work_id = w.work_id WHERE w.work_id IS NULL"),
        ("work_collections.collection_id -> collections",
         "SELECT COUNT(*) FROM work_collections wc LEFT JOIN collections c ON wc.collection_id = c.collection_id WHERE c.collection_id IS NULL"),
        ("work_arc_membership.work_id -> works",
         "SELECT COUNT(*) FROM work_arc_membership wam LEFT JOIN works w ON wam.work_id = w.work_id WHERE w.work_id IS NULL"),
        ("work_arc_membership.arc_id -> story_arcs",
         "SELECT COUNT(*) FROM work_arc_membership wam LEFT JOIN story_arcs sa ON wam.arc_id = sa.arc_id WHERE sa.arc_id IS NULL"),
        ("copies.artifact_id -> artifacts",
         "SELECT COUNT(*) FROM copies c LEFT JOIN artifacts a ON c.artifact_id = a.artifact_id WHERE a.artifact_id IS NULL"),
        ("activity_ledger.work_id -> works",
         "SELECT COUNT(*) FROM activity_ledger al LEFT JOIN works w ON al.work_id = w.work_id WHERE w.work_id IS NULL"),
        ("reading_status.work_id -> works",
         "SELECT COUNT(*) FROM reading_status rs LEFT JOIN works w ON rs.work_id = w.work_id WHERE w.work_id IS NULL"),
        ("creator_roles.creator_id -> creators",
         "SELECT COUNT(*) FROM creator_roles cr LEFT JOIN creators c ON cr.creator_id = c.creator_id WHERE c.creator_id IS NULL"),
    ]

    for name, query in fk_checks:
        orphans = conn.execute(query).fetchone()[0]
        if orphans == 0:
            result.ok(f"FK: {name}")
        else:
            result.fail(f"FK: {name}", f"{orphans} orphaned rows")

    # Every artifact has at least one copy
    no_copy = conn.execute("""
        SELECT COUNT(*) FROM artifacts a
        LEFT JOIN copies c ON a.artifact_id = c.artifact_id
        WHERE c.copy_id IS NULL
    """).fetchone()[0]
    if no_copy == 0:
        result.ok("Every artifact has >= 1 copy")
    else:
        result.fail("Artifacts without copies", f"{no_copy} artifacts")

    # Every artifact linked to at least one work
    no_work = conn.execute("""
        SELECT COUNT(*) FROM artifacts a
        LEFT JOIN artifact_works aw ON a.artifact_id = aw.artifact_id
        WHERE aw.id IS NULL
    """).fetchone()[0]
    if no_work == 0:
        result.ok("Every artifact has >= 1 work")
    else:
        result.fail("Artifacts without works", f"{no_work} artifacts")

    # ===================================================================
    # LAYER 3: Edge Case Spot Checks
    # ===================================================================
    print("\n--- Layer 3: Edge Case Spot Checks ---")

    # Batman #22 dual story with is_partial
    batman22 = conn.execute("""
        SELECT a.title, w.title, aw.position, aw.is_partial
        FROM artifacts a
        JOIN artifact_works aw ON a.artifact_id = aw.artifact_id
        JOIN works w ON aw.work_id = w.work_id
        WHERE a.title = 'Batman #22'
        AND a.source_sheet = 'Comics (Issues)'
        ORDER BY aw.position
    """).fetchall()
    if len(batman22) == 2:
        partial_count = sum(1 for r in batman22 if r[3] == 1)
        if partial_count == 1:
            result.ok("Batman #22 dual-story", f"2 works, 1 partial: {[r[1] for r in batman22]}")
        else:
            result.fail("Batman #22 partial flag", f"Expected 1 partial, got {partial_count}")
    else:
        result.fail("Batman #22 dual-story", f"Expected 2 works, got {len(batman22)}")

    # Dual-arc issue (Snake Eyes + Dogs of War on same work)
    dual_arc = conn.execute("""
        SELECT w.title, GROUP_CONCAT(sa.name, ', ')
        FROM work_arc_membership wam
        JOIN works w ON wam.work_id = w.work_id
        JOIN story_arcs sa ON wam.arc_id = sa.arc_id
        GROUP BY wam.work_id
        HAVING COUNT(DISTINCT sa.arc_id) >= 2
        LIMIT 3
    """).fetchall()
    if dual_arc:
        result.ok("Dual-arc membership found", f"{len(dual_arc)} works with 2+ arcs: {dual_arc[0]}")
    else:
        result.fail("Dual-arc membership", "No works found with membership in 2+ arcs")

    # Hindi ISBNs are strings (not floats/scientific notation)
    hindi_isbns = conn.execute("""
        SELECT title, isbn_or_upc FROM artifacts
        WHERE source_sheet = 'Hindi Books' AND isbn_or_upc IS NOT NULL
    """).fetchall()
    all_valid = True
    for title, isbn in hindi_isbns:
        if isbn and ("e+" in isbn.lower() or "." in isbn):
            result.fail(f"Hindi ISBN for '{title}'", f"Float-like value: {isbn}")
            all_valid = False
    if all_valid and hindi_isbns:
        result.ok("Hindi ISBNs properly formatted", f"{len(hindi_isbns)} valid strings")

    # Novels with ratings have ActivityLedger + ReadingStatus
    rated_novels = conn.execute("""
        SELECT COUNT(DISTINCT al.work_id)
        FROM activity_ledger al
        JOIN works w ON al.work_id = w.work_id
        WHERE w.work_type = 'Novel' AND al.event_type = 'Rated'
    """).fetchone()[0]
    rated_rs = conn.execute("""
        SELECT COUNT(DISTINCT rs.work_id)
        FROM reading_status rs
        JOIN works w ON rs.work_id = w.work_id
        WHERE w.work_type = 'Novel' AND rs.status = 'Finished'
    """).fetchone()[0]
    if rated_novels > 0 and rated_rs > 0:
        result.ok("Novel ratings -> ActivityLedger + ReadingStatus", f"{rated_novels} rated, {rated_rs} with ReadingStatus")
    else:
        result.warn("Novel ratings", f"Ledger: {rated_novels}, ReadingStatus: {rated_rs}")

    # Knightfall arc has correct total_parts
    kf = conn.execute("""
        SELECT name, total_parts FROM story_arcs WHERE name = 'Knightfall'
    """).fetchone()
    if kf and kf[1] == 19:
        result.ok("Knightfall arc", f"total_parts={kf[1]}")
    elif kf:
        result.fail("Knightfall arc total_parts", f"Expected 19, got {kf[1]}")
    else:
        result.fail("Knightfall arc", "Not found")

    # Serialized volume runs (Complete=S mapping)
    serialized = conn.execute("""
        SELECT COUNT(*) FROM volume_runs
        WHERE narrative_format = 'Serialized' AND completion_status = 'Not Pursuing'
    """).fetchone()[0]
    if serialized > 0:
        result.ok("Complete=S mapping", f"{serialized} volume runs marked Serialized + Not Pursuing")
    else:
        result.fail("Complete=S mapping", "No serialized volume runs found")

    # Lent items
    lent_count = conn.execute("SELECT COUNT(*) FROM copies WHERE location = 'Lent'").fetchone()[0]
    if lent_count > 0:
        result.ok("Lent items", f"{lent_count} copies with location=Lent")
    else:
        result.fail("Lent items", "No lent items found")

    # Check data quality flags exist
    flag_count = conn.execute("SELECT COUNT(*) FROM data_quality_flags").fetchone()[0]
    flag_types = conn.execute("""
        SELECT flag_type, COUNT(*) FROM data_quality_flags GROUP BY flag_type
    """).fetchall()
    if flag_count > 0:
        result.ok("Data quality flags generated", f"{flag_count} flags: {dict(flag_types)}")
    else:
        result.warn("Data quality flags", "No flags generated")

    # ===================================================================
    # LAYER 4: Completeness checks
    # ===================================================================
    print("\n--- Layer 4: Completeness ---")

    # Count novels with Goodreads links in source vs DB
    novels_df = pd.read_excel(xlsx, "Novels, etc..")
    source_gr = novels_df["Goodreads Link"].dropna().count()
    db_gr = conn.execute("""
        SELECT COUNT(*) FROM artifacts
        WHERE source_sheet = 'Novels' AND goodreads_url IS NOT NULL
    """).fetchone()[0]
    if source_gr == db_gr:
        result.ok("Novel Goodreads links preserved", f"{source_gr}")
    else:
        result.warn("Novel Goodreads links", f"Source: {source_gr}, DB: {db_gr}")

    # Count novels with series in source vs DB
    source_series = novels_df["Series"].dropna().apply(lambda x: str(x).strip() != "").sum()
    db_series = conn.execute("""
        SELECT COUNT(DISTINCT wc.work_id)
        FROM work_collections wc
        JOIN works w ON wc.work_id = w.work_id
        WHERE w.work_type = 'Novel'
    """).fetchone()[0]
    if source_series == db_series:
        result.ok("Novel series assignments", f"{source_series}")
    else:
        result.warn("Novel series assignments", f"Source: {source_series}, DB: {db_series}")

    # Count dual-story comic issues (Original Volume Issue 2 non-null in source)
    issues_df = pd.read_excel(xlsx, "Comics (Issues)")
    if "Original Volume Issue 2" in issues_df.columns:
        source_dual = issues_df["Original Volume Issue 2"].dropna().apply(lambda x: str(x).strip() != "").sum()
        db_dual = conn.execute("""
            SELECT COUNT(DISTINCT a.artifact_id)
            FROM artifacts a
            JOIN artifact_works aw ON a.artifact_id = aw.artifact_id
            WHERE a.source_sheet = 'Comics (Issues)'
            GROUP BY a.artifact_id
            HAVING COUNT(aw.id) >= 2
        """).fetchone()
        db_dual_count = db_dual[0] if db_dual else 0
        # db_dual_count is just the first group — need to count differently
        db_dual_count = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT a.artifact_id
                FROM artifacts a
                JOIN artifact_works aw ON a.artifact_id = aw.artifact_id
                WHERE a.source_sheet = 'Comics (Issues)'
                GROUP BY a.artifact_id
                HAVING COUNT(aw.id) >= 2
            )
        """).fetchone()[0]
        if source_dual == db_dual_count:
            result.ok("Dual-story comic issues", f"{source_dual}")
        else:
            result.warn("Dual-story comic issues", f"Source: {source_dual}, DB: {db_dual_count}")

    # ===================================================================
    # Summary
    # ===================================================================
    print("\n" + "=" * 55)
    print(f"Verification complete: {result.overall}")
    print(f"  Passed: {result.checks_passed}")
    print(f"  Failed: {result.checks_failed}")

    conn.close()
    return 0 if result.checks_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
