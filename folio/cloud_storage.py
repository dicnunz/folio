"""Durable shared-demo storage with isolated SQLite transactions and remote CAS.

The remote row is authoritative. No local database or process cache is reused.
"""
import base64
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from uuid import uuid4

import requests

from demos.src.coursework_service import RepositoryError
from .storage import AcademicRepository, CourseworkTransaction, SCHEMA_VERSION


class CloudAcademicRepository(AcademicRepository):
    def __init__(self, url, api_key, storage_token):
        if not all(isinstance(value, str) and value.strip() for value in (url, api_key, storage_token)):
            raise RepositoryError("Shared storage configuration is missing.")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise RepositoryError("Shared storage URL must be an HTTPS project URL.")
        self.endpoint = url.rstrip("/") + "/rest/v1/folio_demo_state"
        self.headers = {"apikey": api_key, "x-folio-storage-token": storage_token,
                        "Content-Type": "application/json", "Prefer": "return=representation"}

    def _request(self, method, **kwargs):
        try:
            response = requests.request(method, self.endpoint, headers=self.headers, timeout=15, **kwargs)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as error:
            # Never include HTTP bodies, URLs or credentials in UI-visible errors.
            raise RepositoryError("Shared storage is unavailable. Your save could not be confirmed; reload before trying again.") from error

    def _fetch(self):
        rows = self._request("GET", params={"id": "eq.shared-demo", "select": "id,version,sqlite_base64,mutation_id"})
        if not isinstance(rows, list) or len(rows) > 1:
            raise RepositoryError("Shared storage returned an invalid snapshot.")
        if not rows:
            return None
        row = rows[0]
        if (not isinstance(row, dict) or row.get("id") != "shared-demo"
                or type(row.get("version")) is not int or row["version"] < 1
                or not isinstance(row.get("sqlite_base64"), str)):
            raise RepositoryError("Shared storage returned an invalid snapshot.")
        return row

    @staticmethod
    def _decode(row):
        connection = None
        try:
            payload = base64.b64decode(row["sqlite_base64"], validate=True)
            if not payload.startswith(b"SQLite format 3\x00"):
                raise ValueError("Invalid SQLite header")
            connection = sqlite3.connect(":memory:")
            connection.deserialize(payload)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok" or connection.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("Invalid SQLite contents")
            return connection
        except (sqlite3.Error, ValueError) as error:
            if connection is not None:
                connection.close()
            raise RepositoryError("Shared storage contains an invalid database; it has not been replaced.") from error

    @staticmethod
    def _encoded(connection):
        return base64.b64encode(connection.serialize()).decode("ascii")

    @staticmethod
    def _initial_or_migrated(existing=None):
        try:
            return CloudAcademicRepository._schema_snapshot(existing)
        except (sqlite3.Error, OSError) as error:
            raise RepositoryError("Cannot prepare the shared academic schema.") from error

    @staticmethod
    def _schema_snapshot(existing=None):
        # Use the canonical local initializer so schema rules and migrations have
        # one owner. This private temporary file is deleted before returning.
        with TemporaryDirectory(prefix="folio-schema-") as directory:
            path = Path(directory) / "academic.sqlite3"
            if existing is not None:
                target = sqlite3.connect(path)
                try:
                    existing.backup(target)
                finally:
                    target.close()
            AcademicRepository(path).initialize()
            return base64.b64encode(path.read_bytes()).decode("ascii")

    def _save(self, row, encoded):
        mutation_id = str(uuid4())
        payload = {"sqlite_base64": encoded, "version": row["version"] + 1, "mutation_id": mutation_id}
        try:
            rows = self._request("PATCH", params={"id": "eq.shared-demo", "version": f'eq.{row["version"]}'}, json=payload)
        except RepositoryError:
            # A timeout may follow a successful commit. Confirm this exact write,
            # rather than retrying it or claiming it failed definitively.
            current = self._fetch()
            if current is not None and current.get("mutation_id") == mutation_id:
                return
            raise
        if not isinstance(rows, list):
            raise RepositoryError("Shared storage returned an invalid save confirmation.")
        if len(rows) != 1 or not isinstance(rows[0], dict) or rows[0].get("mutation_id") != mutation_id:
            raise RepositoryError("Someone else saved changes first. Reload and try your change again.")

    def initialize(self):
        row = self._fetch()
        if row is None:
            payload = {"id": "shared-demo", "version": 1,
                       "sqlite_base64": self._initial_or_migrated(), "mutation_id": str(uuid4())}
            try:
                self._request("POST", json=payload)
            except RepositoryError:
                # Includes a concurrent bootstrap's unique-key conflict or an
                # ambiguous response. Never replace the row that won the race.
                row = self._fetch()
                if row is None:
                    raise
            else:
                row = self._fetch()
            if row is None:
                raise RepositoryError("Shared storage initialization could not be confirmed.")
        connection = self._decode(row)
        try:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version != SCHEMA_VERSION:
                encoded = self._initial_or_migrated(connection)
                self._save(row, encoded)
            # Verify the actual application tables too; a well-formed unrelated
            # SQLite file must fail closed instead of being treated as empty.
            else:
                for table in ("coursework", "plans", "tasks", "feedback"):
                    connection.execute(f"SELECT * FROM {table} LIMIT 0")
        except sqlite3.Error as error:
            raise RepositoryError("Shared storage schema is invalid; it has not been replaced.") from error
        finally:
            connection.close()

    def _snapshot(self):
        row = self._fetch()
        if row is None:
            raise RepositoryError("Shared storage has not been initialized.")
        connection = self._decode(row)
        if connection.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            connection.close()
            raise RepositoryError("Shared storage needs initialization before use.")
        return row, connection

    @contextmanager
    def transaction(self):
        row, connection = self._snapshot()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield CourseworkTransaction(connection)
            connection.commit()
            self._save(row, self._encoded(connection))
        except sqlite3.Error as error:
            raise RepositoryError("Shared academic storage failed; changes were not saved.") from error
        finally:
            connection.close()

    @contextmanager
    def _read_snapshot(self):
        _, connection = self._snapshot()
        try:
            connection.execute("BEGIN")
            yield connection
        except sqlite3.Error as error:
            raise RepositoryError("Cannot restore shared academic state.") from error
        finally:
            connection.close()
