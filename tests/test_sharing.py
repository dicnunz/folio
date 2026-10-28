import io
import zipfile
from email import policy
from email.parser import BytesParser
import pytest
from folio.sharing import filter_academic_data, export_docx, export_pdf, prepare_instructor_email

RAW = {'name': 'Résumé <plan>', 'course': 'CSE', 'score': 'SECRET', 'progress': 'SECRET', 'tasks': [{'name': 'Read <chapter>', 'start_time': '2026-10-22T10:00', 'end_time': '2026-10-22T11:00', 'completed': 'SECRET', 'xp': 'SECRET'}]}

def test_allowlist_applies_to_every_output():
    data = filter_academic_data(RAW, list(RAW), [0])
    assert 'score' not in data and 'progress' not in data
    assert 'completed' not in data['tasks'][0]
    docx = export_docx(RAW)
    with zipfile.ZipFile(io.BytesIO(docx)) as archive:
        for name in archive.namelist():
            assert b'SECRET' not in archive.read(name)
        assert b'&lt;chapter&gt;' in archive.read('word/document.xml')
    pdf = export_pdf(RAW)
    assert pdf.startswith(b'%PDF') and b'SECRET' not in pdf
    mail = BytesParser(policy=policy.default).parsebytes(prepare_instructor_email(data))
    assert 'Read <chapter>' in mail.get_body(preferencelist=('plain',)).get_content()
    assert len(list(mail.iter_attachments())) == 2
    assert b'SECRET' not in prepare_instructor_email(RAW)

def test_header_injection_rejected():
    with pytest.raises(ValueError):
        prepare_instructor_email(RAW, subject='Hello\nBcc: bad@example.com')

def test_empty_selection():
    assert filter_academic_data(RAW, [], []) == {}

def test_real_repository(tmp_path):
    from folio.storage import AcademicRepository
    from folio.sharing import get_shareable_academic_data
    repository = AcademicRepository(tmp_path / 'academic.db')
    repository.initialize()
    coursework = repository.store_coursework('CREATE', {'course': 'CSE', 'item_name': 'Essay', 'due_date': '2026-10-25', 'score': 99})
    saved = repository.store_plan_data({'coursework_id': coursework['id'], 'name': 'Essay plan'}, [{'name': 'Draft', 'start_time': '2026-10-22T10:00', 'end_time': '2026-10-22T11:00', 'completed': True}])
    data = get_shareable_academic_data(repository, saved['plan']['id'], ['course', 'tasks', 'score'], [0])
    assert data == {'course': 'CSE', 'tasks': [{'name': 'Draft', 'start_time': '2026-10-22T10:00', 'end_time': '2026-10-22T11:00'}]}
    assert 'Tasks:' not in __import__('folio.sharing', fromlist=['preview_text']).preview_text({'name': 'Only name'})

def test_private_changes_never_change_academic_content():
    from folio.sharing import preview_text
    private = ('progress', 'score', 'xp', 'points', 'level', 'badge', 'cosmetic', 'game', 'preferences')
    first = {**RAW, **{key: f'PRIVATE_{key}' for key in private}}
    second = {**first, **{key: f'ALTERED_{key}' for key in private}}
    selection = list(first)
    assert filter_academic_data(first, selection) == filter_academic_data(second, selection)
    assert preview_text(first) == preview_text(second)
    message = BytesParser(policy=policy.default).parsebytes(prepare_instructor_email(first))
    for attachment in message.iter_attachments():
        payload = attachment.get_payload(decode=True)
        if attachment.get_filename().endswith('.docx'):
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                contents = b' '.join(archive.read(name) for name in archive.namelist())
        else:
            contents = payload
        for key in private:
            assert f'PRIVATE_{key}'.encode() not in contents

def test_pdf_extracted_text_and_metadata(tmp_path):
    import shutil
    import subprocess
    if shutil.which('pdftotext') is None:
        pytest.skip('Poppler is needed for independent PDF extraction')
    data = {**RAW, 'tasks': [*RAW['tasks'], {'name': 'UNSELECTED_TASK'}]}
    selected = filter_academic_data(data, ['course', 'tasks', 'score', 'progress'], [0])
    path = tmp_path / 'selected.pdf'
    path.write_bytes(export_pdf(selected))
    text = subprocess.check_output(['pdftotext', str(path), '-']).decode()
    assert 'CSE' in text and 'Read <chapter>' in text
    assert 'SECRET' not in text and 'UNSELECTED_TASK' not in text and 'Résumé' not in text
    if shutil.which('pdfinfo'):
        metadata = subprocess.check_output(['pdfinfo', str(path)]).decode()
        assert 'SECRET' not in metadata and 'UNSELECTED_TASK' not in metadata

def test_nested_private_structures_in_allowed_fields_are_dropped(tmp_path):
    from folio.sharing import ACADEMIC_FIELDS, preview_text
    hostile = {key: {'xp': 'NESTED_PRIVATE'} for key in ACADEMIC_FIELDS if key != 'tasks'}
    hostile['tasks'] = [{'name': {'badge': 'NESTED_PRIVATE'}, 'start_time': ['NESTED_PRIVATE'], 'end_time': '2026-10-22T11:00', 'completed': 'NESTED_PRIVATE'}]
    assert filter_academic_data(hostile) == {'tasks': [{'end_time': '2026-10-22T11:00'}]}
    assert 'NESTED_PRIVATE' not in preview_text(hostile)
    for output in (export_pdf(hostile), export_docx(hostile), prepare_instructor_email(hostile)):
        assert b'NESTED_PRIVATE' not in output
    with zipfile.ZipFile(io.BytesIO(export_docx(hostile))) as archive:
        assert all(b'NESTED_PRIVATE' not in archive.read(name) for name in archive.namelist())
