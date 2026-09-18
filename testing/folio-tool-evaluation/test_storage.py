import json
from pathlib import Path

from tinydb import TinyDB, Query


RECORDS = [
   {"id": "A1", "assignment": "Design Review", "course": "CS 491", "priority": "High", "due_date": "2026-09-30"},
   {"id": "A2", "assignment": "Lab 2", "course": "CS 491", "priority": "Medium", "due_date": "2026-10-02"},
]


def sqlite_candidate(path: Path):
   import sqlite3

   conn = sqlite3.connect(path)
   conn.execute("CREATE TABLE assignments (id TEXT PRIMARY KEY, assignment TEXT, course TEXT, priority TEXT, due_date TEXT)")
   conn.executemany("INSERT INTO assignments VALUES (?, ?, ?, ?, ?)", [(r["id"], r["assignment"], r["course"], r["priority"], r["due_date"]) for r in RECORDS])
   conn.commit()

   rows = conn.execute("SELECT * FROM assignments WHERE priority = 'High' ORDER BY due_date").fetchall()
   assert rows[0][1] == "Design Review"

   conn.execute("UPDATE assignments SET priority = 'Very High' WHERE id = 'A1'")
   conn.execute("INSERT INTO assignments (id, assignment, course, priority, due_date) VALUES (?, ?, ?, ?, ?)", ("A3", "Final Report", "CS 491", "High", "2026-10-12"))
   conn.commit()

   conn.execute("DELETE FROM assignments WHERE id = 'A2'")
   conn.commit()

   reloaded = conn.execute("SELECT id, assignment, priority FROM assignments ORDER BY due_date").fetchall()
   assert reloaded[0][1] == "Design Review"
   assert reloaded[-1][1] == "Final Report"
   conn.close()
   return reloaded


def json_candidate(path: Path):
   data = {"assignments": RECORDS}
   path.write_text(json.dumps(data, indent=2))
   loaded = json.loads(path.read_text())
   high = [r for r in loaded["assignments"] if r["priority"] == "High"]
   assert high[0]["assignment"] == "Design Review"
   loaded["assignments"][0]["priority"] = "Very High"
   loaded["assignments"].append({"id": "A3", "assignment": "Final Report", "course": "CS 491", "priority": "High", "due_date": "2026-10-12"})
   loaded["assignments"] = [r for r in loaded["assignments"] if r["id"] != "A2"]
   path.write_text(json.dumps(loaded, indent=2))
   reloaded = json.loads(path.read_text())
   assert reloaded["assignments"][0]["priority"] == "Very High"
   assert reloaded["assignments"][-1]["assignment"] == "Final Report"
   return reloaded


def tinydb_candidate(path: Path):
   db = TinyDB(path)
   db.truncate()
   db.insert_multiple(RECORDS)
   high = db.search(Query().priority == "High")
   assert high[0]["assignment"] == "Design Review"
   db.update({"priority": "Very High"}, Query().id == "A1")
   db.insert({"id": "A3", "assignment": "Final Report", "course": "CS 491", "priority": "High", "due_date": "2026-10-12"})
   db.remove(Query().id == "A2")
   reloaded = db.all()
   assert reloaded[0]["priority"] == "Very High"
   assert reloaded[-1]["assignment"] == "Final Report"
   db.close()
   return reloaded


def test_storage_candidates(tmp_path):
   sqlite_results = sqlite_candidate(tmp_path / "assignments.sqlite")
   json_results = json_candidate(tmp_path / "assignments.json")
   tinydb_results = tinydb_candidate(tmp_path / "tinydb.json")

   assert sqlite_results[-1][1] == "Final Report"
   assert json_results["assignments"][-1]["assignment"] == "Final Report"
   assert tinydb_results[-1]["assignment"] == "Final Report"


def test_storage_invalid_record_rejected(tmp_path):
   bad = tmp_path / "bad.json"
   bad.write_text(json.dumps({"assignments": [{"id": "", "assignment": "", "priority": None}] }))
   payload = json.loads(bad.read_text())
   invalid = [r for r in payload["assignments"] if not r.get("id") or not r.get("assignment") or r.get("priority") is None]
   assert invalid
