"""
One-shot data migration: SQLite → MySQL via Django ORM.

Usage:
    1. Ensure MySQL is running and the database exists
    2. Set DB_* environment variables or edit config/settings.py
    3. Run: python manage.py migrate          (create MySQL schema)
    4. Run: python migrate_sqlite_to_mysql.py  (transfer data)

This script reads from the existing SQLite database (data/app.db)
and writes to MySQL through Django ORM models.
"""

from datetime import datetime
import os
import sqlite3
import sys

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from api.models import (
    Device,
    Element,
    Page,
    PageFlow,
    TestDefinition,
    TestExecutionResult,
)

# Path to existing SQLite database
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "data", "app.db")


def connect_sqlite():
    """Open the SQLite database with Row factory."""
    if not os.path.exists(SQLITE_PATH):
        print(f"ERROR: SQLite database not found at {SQLITE_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_datetime(val):
    """Parse a datetime string from SQLite to Python datetime or None."""
    if not val:
        return None
    try:
        # Try ISO format
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        try:
            # Try SQLite format: "YYYY-MM-DD HH:MM:SS"
            return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return None


def migrate_devices(src):
    """Migrate devices table."""
    print("[1/7] Migrating devices...")
    count = 0
    for row in src.execute("SELECT * FROM devices"):
        Device.objects.update_or_create(
            serial=row["serial"],
            defaults={
                "name": row["name"] or "",
                "created_at": parse_datetime(row["created_at"]),
            },
        )
        count += 1
    print(f"  → {count} devices migrated")


def migrate_pages(src):
    """Migrate pages table."""
    print("[2/7] Migrating pages...")
    count = 0
    for row in src.execute("SELECT * FROM pages"):
        Page.objects.update_or_create(
            id=row["id"],
            defaults={
                "device_id": row["device_id"],
                "label": row["label"] or "",
                "package": row["package"] or "",
                "activity": row["activity"] or "",
                "screenshot_path": row["screenshot_path"] or "",
                "element_count": row["element_count"] or 0,
                "created_at": parse_datetime(row["created_at"]),
            },
        )
        count += 1
    print(f"  → {count} pages migrated")


def migrate_elements(src):
    """Migrate elements table."""
    print("[3/7] Migrating elements...")
    count = 0
    for row in src.execute("SELECT * FROM elements"):
        Element.objects.update_or_create(
            id=row["id"],
            defaults={
                "page_id": row["page_id"],
                "class_name": row["class_name"] or "",
                "text_val": row["text_val"] or "",
                "content_desc": row["content_desc"] or "",
                "resource_id": row["resource_id"] or "",
                "bounds": row["bounds"] or "",
                "xpath_candidates": row["xpath_candidates"] or "[]",
                "clickable": bool(row["clickable"]),
                "enabled": bool(row["enabled"]),
                "alias": row["alias"] or "",
                "tags": row["tags"] or "",
                "is_test_point": bool(row["is_test_point"]),
                "notes": row["notes"] or "",
                "created_at": parse_datetime(row["created_at"]),
            },
        )
        count += 1
    print(f"  → {count} elements migrated")


def migrate_page_flows(src):
    """Migrate page_flows table."""
    print("[4/7] Migrating page_flows...")
    count = 0
    for row in src.execute("SELECT * FROM page_flows"):
        PageFlow.objects.update_or_create(
            id=row["id"],
            defaults={
                "from_page_id": row["from_page_id"],
                "to_page_id": row["to_page_id"],
                "trigger_element_id": row["trigger_element_id"],
                "trigger_action": row["trigger_action"] or "click",
                "created_at": parse_datetime(row["created_at"]),
            },
        )
        count += 1
    print(f"  → {count} page_flows migrated")


def migrate_test_definitions(src):
    """Migrate test_definitions table."""
    print("[6/7] Migrating test_definitions...")
    count = 0
    for row in src.execute("SELECT * FROM test_definitions"):
        TestDefinition.objects.update_or_create(
            id=row["id"],
            defaults={
                "title": row["title"] or "",
                "category": row["category"] or "",
                "description": row["description"] or "",
                "steps": row["steps"] or "",
                "steps_json": row["steps_json"] or "[]",
                "enabled": bool(row["enabled"]),
                "package_name": row["package_name"] or "",
                "created_at": parse_datetime(row["created_at"]),
                "updated_at": parse_datetime(row["updated_at"]),
            },
        )
        count += 1
    print(f"  → {count} test_definitions migrated")


def migrate_test_results(src):
    """Migrate test_results table."""
    print("[7/7] Migrating test_results...")
    count = 0
    for row in src.execute("SELECT * FROM test_results"):
        TestExecutionResult.objects.update_or_create(
            id=row["id"],
            defaults={
                "run_id": row["run_id"],
                "case_id": row["case_id"],
                "iteration": row["iteration"],
                "result": row["result"],
                "duration_ms": float(row["duration_ms"] or 0),
                "detail": row["detail"] or "",
                "created_at": parse_datetime(row["created_at"]),
            },
        )
        count += 1
    print(f"  → {count} test_results migrated")


def verify():
    """Verify row counts match between SQLite and MySQL."""
    print("\n=== Verification ===")
    src = connect_sqlite()

    tables = [
        ("devices", Device),
        ("pages", Page),
        ("elements", Element),
        ("page_flows", PageFlow),
        ("test_definitions", TestDefinition),
        ("test_results", TestExecutionResult),
    ]

    all_ok = True
    for table_name, model in tables:
        sqlite_count = src.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        mysql_count = model.objects.count()
        status = "✓" if sqlite_count == mysql_count else "✗ MISMATCH"
        if sqlite_count != mysql_count:
            all_ok = False
        print(f"  {status} {table_name}: SQLite={sqlite_count}, MySQL={mysql_count}")

    src.close()

    if all_ok:
        print("\n✓ All tables migrated successfully!")
    else:
        print("\n⚠ Some tables have mismatched counts. Please investigate.")


def main():
    print("=" * 50)
    print("  SQLite → MySQL Data Migration")
    print(f"  Source: {SQLITE_PATH}")
    print("=" * 50)

    src = connect_sqlite()

    try:
        migrate_devices(src)
        migrate_pages(src)
        migrate_elements(src)
        migrate_page_flows(src)
        migrate_test_definitions(src)
        migrate_test_results(src)
    finally:
        src.close()

    verify()


if __name__ == "__main__":
    main()
