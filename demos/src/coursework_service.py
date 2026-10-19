"""Application services. Repositories own atomic transactions and relationships.

Repository contract: transaction() yields an object with list_records(), get(id),
insert(record, source), update(id, record), dependencies(id), delete(id).
Writes return saved dictionaries. dependencies returns a collection, or None when
relationships cannot be checked. Storage adapters translate failures to
RepositoryError. An exception leaving transaction() MUST roll back all writes.
"""

from .coursework import duplicate_key, parse_csv, validate_and_deduplicate, validate_coursework


class RepositoryError(Exception):
    """A repository operation failed and its transaction was rolled back."""


def failure(code, message, field="_record"):
    return {"success": False, "record": None,
            "errors": [{"field": field, "code": code, "message": message}]}


class CourseworkService:
    def __init__(self, repository):
        self.repository = repository

    def create_coursework(self, coursework_data):
        result = validate_coursework(coursework_data)
        if result["errors"]:
            return {"success": False, "record": None, "errors": result["errors"]}
        try:
            with self.repository.transaction() as repository:
                if any(duplicate_key(row) == duplicate_key(result["record"])
                       for row in repository.list_records()):
                    return failure("duplicate", "Coursework with identical required fields already exists.")
                saved = repository.insert(result["record"], "manual")
            return {"success": True, "record": saved, "errors": []}
        except RepositoryError as error:
            return failure("storage", str(error))

    def edit_coursework(self, coursework_id, changes):
        try:
            with self.repository.transaction() as repository:
                original = repository.get(coursework_id)
                if original is None:
                    return failure("not_found", "Coursework was not found.")
                editable = {key: value for key, value in original.items()
                            if key not in ("id", "source")}
                result = validate_coursework({**editable, **changes})
                if result["errors"]:
                    return {"success": False, "record": None, "errors": result["errors"]}
                if any(row["id"] != coursework_id and
                       duplicate_key(row) == duplicate_key(result["record"])
                       for row in repository.list_records()):
                    return failure("duplicate", "Coursework with identical required fields already exists.")
                saved = repository.update(coursework_id, result["record"])
            return {"success": True, "record": saved, "errors": []}
        except RepositoryError as error:
            return failure("storage", str(error))

    def delete_coursework(self, coursework_id):
        try:
            with self.repository.transaction() as repository:
                original = repository.get(coursework_id)
                if original is None:
                    return failure("not_found", "Coursework was not found.")
                dependencies = repository.dependencies(coursework_id)
                if dependencies is None:
                    return failure("relationships_unknown", "Plan/task relationships cannot be checked; deletion was not performed.")
                if dependencies:
                    return failure("dependent_records", "Coursework is referenced by plans or tasks; deletion was not performed.")
                repository.delete(coursework_id)
            return {"success": True, "record": original, "errors": []}
        except RepositoryError as error:
            return failure("storage", str(error))

    def import_coursework_csv(self, csv_file, source=None):
        parsed = parse_csv(csv_file, source)
        summary = {"success": False, "total_rows": len(parsed["rows"]),
                   "inserted_rows": 0, "accepted_count": 0, "rejected_count": 0,
                   "invalid_rows": 0, "duplicate_rows": 0, "errors": [],
                   "file_errors": parsed["file_errors"], "storage_errors": [],
                   "records": [], "source": parsed["source"]}
        if parsed["file_errors"]:
            return summary
        try:
            with self.repository.transaction() as repository:
                classified = validate_and_deduplicate(
                    parsed["rows"], (duplicate_key(row) for row in repository.list_records()))
                summary["errors"] = classified["rejected"]
                summary["duplicate_rows"] = sum(
                    any(error["code"] == "duplicate" for error in row["field_errors"])
                    for row in classified["rejected"])
                summary["invalid_rows"] = len(classified["rejected"]) - summary["duplicate_rows"]
                saved = [repository.insert(row["record"], "csv")
                         for row in classified["accepted"]]
            summary.update(success=True, records=saved, inserted_rows=len(saved),
                           accepted_count=len(saved), rejected_count=len(classified["rejected"]))
        except RepositoryError as error:
            summary["storage_errors"] = [str(error)]
            # Valid rows that could not be committed are also rejected, with locations.
            rejected_locations = {row["row_number"] for row in summary["errors"]}
            for row in parsed["rows"]:
                if row["row_number"] not in rejected_locations:
                    summary["errors"].append({**row, "errors": [str(error)],
                        "field_errors": [{"field": "_row", "code": "storage", "message": str(error)}]})
            summary["errors"].sort(key=lambda row: row["row_number"])
            summary["rejected_count"] = summary["total_rows"]
        return summary
