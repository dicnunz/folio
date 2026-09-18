"""Small runnable demonstration of CSV validation and SQLite storage."""

import csv
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import csv_storage


def create_sample_csv(csv_path):
    """Write a tiny input containing valid, invalid, and duplicate rows."""
    rows = [
        {
            "course": "Calculus",
            "item_name": "Chapter 5 Review",
            "due_date": "2026-09-20",
            "score": "92",
        },
        {
            "course": "",
            "item_name": "Missing Course",
            "due_date": "2026-09-21",
            "score": "80",
        },
        {
            "course": "Calculus",
            "item_name": "Chapter 5 Review",
            "due_date": "2026-09-20",
            "score": "92",
        },
        {
            "course": "Software Engineering",
            "item_name": "Design Document",
            "due_date": "2026-09-22",
            "score": "88.5",
        },
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_storage.REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    print("--- Folio CSV/SQLite Demo ---")
    with tempfile.TemporaryDirectory() as temporary_directory:
        temp_path = Path(temporary_directory)
        csv_path = temp_path / "sample.csv"
        database_path = temp_path / "folio.db"

        create_sample_csv(csv_path)
        summary = csv_storage.import_csv(csv_path, database_path)

        print("Import summary:")
        for key in ("total_rows", "inserted_rows", "invalid_rows", "duplicate_rows"):
            print(f"  {key}: {summary[key]}")

        print("Stored records:")
        for record in csv_storage.get_all_records(database_path):
            print(f"  {record}")


if __name__ == "__main__":
    main()
