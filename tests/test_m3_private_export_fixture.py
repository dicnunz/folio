from email import policy
from email.parser import BytesParser
from io import BytesIO
import shutil
import subprocess
import zipfile

import pytest

from folio.sharing import (
    export_docx, export_pdf, filter_academic_data,
    prepare_instructor_email, preview_text,
)


@pytest.mark.parametrize("prefix", ["PRIVATE", "CHANGED-PRIVATE"])
def test_private_follow_through_fields_stay_out_of_selected_exports(tmp_path, prefix):
    if not shutil.which("pdftotext") or not shutil.which("pdfinfo"):
        pytest.skip("Poppler required to inspect PDF text and metadata")
    private_markers = tuple(
        f"{prefix}-{field}" for field in ("COMPLETION", "PROGRESS", "REMINDER", "REWARD")
    )
    foreign = "UNSELECTED-WALKTHROUGH-TASK"
    selected = "SELECTED-WALKTHROUGH-TASK"
    mixed = {
        "name": "Synthetic M3 plan",
        "progress": private_markers[1],
        "reward": private_markers[3],
        "tasks": [
            {
                "name": selected,
                "start_time": "2026-11-20T09:00",
                "end_time": "2026-11-20T09:45",
                "completed": private_markers[0],
                "reminder": private_markers[2],
            },
            {"name": foreign},
        ],
    }
    chosen = filter_academic_data(mixed, tuple(mixed), [0])
    assert chosen["tasks"] == [{
        "name": selected,
        "start_time": "2026-11-20T09:00",
        "end_time": "2026-11-20T09:45",
    }]
    assert set(chosen) == {"name", "tasks"}

    def inspect_text(body):
        assert selected in body
        assert all(marker not in body for marker in (foreign, *private_markers))

    def inspect_pdf(data, filename):
        path = tmp_path / filename
        path.write_bytes(data)
        inspect_text(subprocess.check_output(["pdftotext", str(path), "-"], text=True))
        metadata = subprocess.check_output(["pdfinfo", str(path)], text=True)
        assert all(marker not in metadata for marker in (foreign, *private_markers))

    def inspect_docx(data):
        with zipfile.ZipFile(BytesIO(data)) as docx:
            assert docx.testzip() is None
            inspect_text(docx.read("word/document.xml").decode())
            for path in docx.namelist():
                assert all(
                    marker.encode() not in docx.read(path)
                    for marker in (foreign, *private_markers)
                )

    inspect_text(preview_text(chosen))
    inspect_pdf(export_pdf(chosen), "direct.pdf")
    inspect_docx(export_docx(chosen))
    unsent_bytes = prepare_instructor_email(chosen, recipient="advisor@example.test")
    unsent = BytesParser(policy=policy.default).parsebytes(unsent_bytes)
    assert unsent["Subject"]
    assert all(marker not in str(unsent["Subject"]) for marker in (foreign, *private_markers))
    inspect_text(unsent.get_body(preferencelist=("plain",)).get_content())
    parts = {item.get_filename(): item.get_payload(decode=True) for item in unsent.iter_attachments()}
    assert set(parts) == {"academic-plan.pdf", "academic-plan.docx"}
    inspect_pdf(parts["academic-plan.pdf"], "attachment.pdf")
    inspect_docx(parts["academic-plan.docx"])
