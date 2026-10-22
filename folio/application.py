"""Startup composition shared by the local app and integration tests."""
import os
from pathlib import Path

from demos.src.coursework_service import CourseworkService
from .storage import AcademicRepository


def open_application(database_path=None):
    path = database_path or os.environ.get("FOLIO_DATABASE") or Path(__file__).resolve().parents[1] / "data" / "academic.sqlite3"
    repository = AcademicRepository(path)
    repository.initialize()
    return repository, CourseworkService(repository)
