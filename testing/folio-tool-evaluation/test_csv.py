import csv
from pathlib import Path

import pandas as pd
import polars as pl


CSV_ROWS = [
   {"assignment": "Design Review", "course": "CS 491", "priority": "High", "due_date": "2026-09-30", "points": "10"},
   {"assignment": "Lab 2", "course": "CS 491", "priority": "Medium", "due_date": "2026-10-02", "points": "5"},
   {"assignment": "Reading", "course": "ENG 210", "priority": "Low", "due_date": "2026-10-01", "points": "2"},
]


def csv_candidate(path: Path):
   with path.open("w", newline="") as f:
      writer = csv.DictWriter(f, fieldnames=["assignment", "course", "priority", "due_date", "points"])
      writer.writeheader()
      writer.writerows(CSV_ROWS)

   with path.open(newline="") as f:
      rows = list(csv.DictReader(f))
   filtered = [row for row in rows if row["priority"] == "High"]
   filtered[0]["points"] = "12"
   filtered.append({"assignment": "Final Report", "course": "CS 491", "priority": "High", "due_date": "2026-10-12", "points": "15"})
   filtered = sorted(filtered, key=lambda row: row["due_date"])

   out = path.with_name("filtered.csv")
   with out.open("w", newline="") as f:
      writer = csv.DictWriter(f, fieldnames=["assignment", "course", "priority", "due_date", "points"])
      writer.writeheader()
      writer.writerows(filtered)

   with out.open(newline="") as f:
      reloaded = list(csv.DictReader(f))
   assert reloaded[0]["assignment"] == "Design Review"
   assert reloaded[-1]["assignment"] == "Final Report"
   return reloaded


def pandas_candidate(path: Path):
   df = pd.DataFrame(CSV_ROWS)
   filtered = df[df["priority"] == "High"].copy()
   filtered.loc[filtered.index[0], "points"] = 12
   filtered = pd.concat([filtered, pd.DataFrame([{"assignment": "Final Report", "course": "CS 491", "priority": "High", "due_date": "2026-10-12", "points": 15}])], ignore_index=True)
   filtered = filtered.sort_values("due_date").reset_index(drop=True)
   out = path.with_name("pandas_export.csv")
   filtered.to_csv(out, index=False)
   reloaded = pd.read_csv(out)
   assert reloaded.iloc[0]["assignment"] == "Design Review"
   assert reloaded.iloc[-1]["assignment"] == "Final Report"
   return reloaded


def polars_candidate(path: Path):
   df = pl.DataFrame(CSV_ROWS)
   filtered = df.filter(pl.col("priority") == "High")
   filtered = filtered.with_columns(pl.col("points").cast(pl.Int64))
   filtered = filtered.with_row_index().with_columns([
      pl.when(pl.col("index") == 0).then(pl.lit(12)).otherwise(pl.col("points")).alias("points")
   ]).drop("index")
   new_row = pl.DataFrame([{"assignment": "Final Report", "course": "CS 491", "priority": "High", "due_date": "2026-10-12", "points": 15}])
   filtered = pl.concat([filtered, new_row], how="vertical")
   filtered = filtered.sort("due_date")
   out = path.with_name("polars_export.csv")
   filtered.write_csv(out)
   reloaded = pl.read_csv(out)
   assert reloaded[0, "assignment"] == "Design Review"
   assert reloaded[-1, "assignment"] == "Final Report"
   return reloaded


def test_csv_candidates(tmp_path):
   base = tmp_path / "assignments.csv"
   standard = csv_candidate(base)
   pandas = pandas_candidate(base)
   polars = polars_candidate(base)

   assert standard[0]["priority"] == "High"
   assert pandas.iloc[0]["points"] == 12
   assert polars[0, "points"] == 12


def test_csv_malformed_input(tmp_path):
   bad = tmp_path / "bad.csv"
   bad.write_text("assignment,course,priority\nDesign Review,CS 491,High\nBroken,,\n")
   with __import__("pytest").raises((ValueError, KeyError, TypeError)):
      rows = list(csv.DictReader(bad.open(newline="")))
      for row in rows:
            if not row.get("assignment") or not row.get("priority"):
               raise ValueError("Missing required CSV value")
