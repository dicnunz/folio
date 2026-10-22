"""Coursework validation and CSV parsing, independent of storage and UI."""

import csv
import io
import math
import re
from datetime import date, datetime
from pathlib import Path

REQUIRED_COLUMNS = ("course", "item_name", "due_date")
OPTIONAL_COLUMNS = ("score", "start_time", "end_time")


def normalize_row(row):
    normalized = {key: value.strip() if isinstance(value, str) else value
                  for key, value in row.items()}
    if type(normalized.get("due_date")) is date:
        normalized["due_date"] = normalized["due_date"].isoformat()
    score = normalized.get("score")
    if score in (None, ""):
        normalized["score"] = None
    elif not isinstance(score, bool):
        try:
            normalized["score"] = float(score)
        except (TypeError, ValueError, OverflowError):
            pass
    for field in ("start_time", "end_time"):
        if normalized.get(field) in (None, ""):
            normalized[field] = None
    return normalized


def validate_coursework(data):
    """Return normalized data and every field error; never mutate the input."""
    row = normalize_row(data)
    errors = []

    def error(field, code, message):
        errors.append({"field": field, "code": code, "message": message})

    for field in REQUIRED_COLUMNS:
        if row.get(field) in (None, ""):
            error(field, "required", f"{field} is required.")
    for field in ("course", "item_name"):
        if row.get(field) not in (None, "") and not isinstance(row[field], str):
            error(field, "type", f"{field} must be text.")
    value = row.get("due_date")
    if value not in (None, ""):
        try:
            if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError
            date.fromisoformat(value)
        except ValueError:
            error("due_date", "format", "due_date must use YYYY-MM-DD format.")
    parsed_times = {}
    for field in ("start_time", "end_time"):
        value = row.get(field)
        if value is not None:
            try:
                if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", value):
                    raise ValueError
                parsed_times[field] = datetime.strptime(value, "%Y-%m-%dT%H:%M")
            except ValueError:
                error(field, "format", f"{field} must use YYYY-MM-DDTHH:MM format (24-hour local time).")
    if row.get("start_time") is not None and row.get("end_time") is None:
        error("end_time", "required", "end_time is required when start_time is supplied.")
    if row.get("end_time") is not None and row.get("start_time") is None:
        error("start_time", "required", "start_time is required when end_time is supplied.")
    if len(parsed_times) == 2 and parsed_times["end_time"] <= parsed_times["start_time"]:
        error("end_time", "order", "end_time must be later than start_time.")
    score = row.get("score")
    if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float))):
        error("score", "type", "score must be numeric.")
    elif score is not None and not math.isfinite(score):
        error("score", "format", "score must be finite.")
    if None in row:
        error("_row", "columns", "Row contains more values than the CSV header.")
    for field in row:
        if field is not None and field not in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
            error(field, "unsupported", f"Unsupported coursework field: {field}.")
    return {"record": row, "errors": errors}


def duplicate_key(row):
    return tuple(row[field] for field in REQUIRED_COLUMNS)


def parse_csv(csv_file, source=None):
    """Read a path or text/binary stream; locations are physical start/end lines.

    Caller-owned streams stay open and are read from their current position.
    File failures discard all parsed rows, including any valid prefix.
    """
    label = source or str(getattr(csv_file, "name", "csv"))
    try:
        if isinstance(csv_file, (str, Path)):
            label = source or str(csv_file)
            text = Path(csv_file).read_text(encoding="utf-8-sig")
        else:
            text = csv_file.read()
            if isinstance(text, bytes):
                text = text.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text.lstrip("\ufeff"), newline=""), strict=True)
        headers = next(reader, [])
        missing = set(REQUIRED_COLUMNS) - set(headers)
        if missing:
            raise ValueError("CSV is missing required columns: " + ", ".join(sorted(missing)))
        if len(headers) != len(set(headers)) or "" in headers:
            raise ValueError("CSV headers must be nonblank and unique.")
        unknown = set(headers) - set(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
        if unknown:
            raise ValueError("Unsupported CSV columns: " + ", ".join(sorted(unknown)))
        rows = []
        while True:
            start = reader.line_num + 1
            values = next(reader, None)
            if values is None:
                break
            if not values:
                continue
            row = dict(zip(headers, values))
            if len(values) > len(headers):
                row[None] = values[len(headers):]
            rows.append({"row_number": start, "end_row_number": reader.line_num,
                         "source": label, "record": row})
        return {"rows": rows, "file_errors": [], "source": label}
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        return {"rows": [], "file_errors": [str(error)], "source": label}


def validate_and_deduplicate(rows, existing_keys=()):
    """Classify parsed rows; rejected duplicates count once, as rejected rows."""
    seen = set(existing_keys)
    accepted, rejected = [], []
    for entry in rows:
        result = validate_coursework(entry["record"])
        errors = result["errors"]
        if not errors:
            key = duplicate_key(result["record"])
            if key in seen:
                errors = [{"field": "_row", "code": "duplicate",
                           "message": "Coursework with identical required fields already exists."}]
            else:
                seen.add(key)
        item = {**entry, "record": result["record"], "field_errors": errors,
                "errors": [error["message"] for error in errors]}
        (rejected if errors else accepted).append(item)
    return {"accepted": accepted, "rejected": rejected}
