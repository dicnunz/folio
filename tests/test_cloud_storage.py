import base64
from copy import deepcopy
import sqlite3
import pytest
import requests
from demos.src.coursework_service import RepositoryError
from folio.cloud_storage import CloudAcademicRepository
from folio.storage import SCHEMA, SCHEMA_VERSION

class Response:
    def __init__(self, data, status=200):
        self.data, self.status = deepcopy(data), status
    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError('private server details')
    def json(self):
        return self.data

class Remote:
    def __init__(self):
        self.row = None
        self.fail_before_patch = False
        self.timeout_after_patch = False
        self.bootstrap_winner = None
        self.calls = []
    def request(self, method, url, *, headers, timeout, params=None, json=None):
        assert url == 'https://example.supabase.co/rest/v1/folio_demo_state'
        assert headers['apikey'] == 'publishable'
        assert headers['x-folio-storage-token'] == 'private-token'
        assert headers['Prefer'] == 'return=representation'
        assert timeout > 0
        self.calls.append(method)
        if method == 'GET':
            assert params['id'] == 'eq.shared-demo'
            return Response([self.row] if self.row is not None else [])
        if method == 'POST':
            if self.bootstrap_winner is not None:
                self.row = deepcopy(self.bootstrap_winner)
            if self.row is not None:
                return Response({}, 409)
            self.row = deepcopy(json)
            return Response([self.row], 201)
        if method == 'PATCH':
            if self.fail_before_patch:
                raise requests.ConnectionError('secret transport information')
            assert params['id'] == 'eq.shared-demo'
            if params['version'] != f'eq.{self.row["version"]}':
                return Response([])
            self.row.update(deepcopy(json))
            if self.timeout_after_patch:
                raise requests.Timeout('response lost after commit')
            return Response([self.row])
        raise AssertionError(method)

def repository():
    return CloudAcademicRepository('https://example.supabase.co', 'publishable', 'private-token')
@pytest.fixture
def remote(monkeypatch):
    remote = Remote()
    monkeypatch.setattr('folio.cloud_storage.requests.request', remote.request)
    return remote

def coursework(name='Essay'):
    return {'course': 'English', 'item_name': name, 'due_date': '2026-11-01', 'source': 'manual'}

def test_aggregate_survives_fresh_repository_and_initialization(remote):
    first = repository()
    first.initialize()
    item = first.store_coursework('CREATE', coursework())
    saved = first.store_plan_data({'coursework_id': item['id'], 'name': 'Essay plan'},
        tasks=[{'name': 'Draft', 'start_time': '2026-10-30T09:00', 'end_time': '2026-10-30T10:00'}],
        feedback=[{'suggestion': 'Add sources'}])
    expected = first.restore_saved_application_state()
    second = repository()
    second.initialize()
    assert second.restore_saved_application_state() == expected
    assert second.get_plan(saved['plan']['id']) == saved
    second.delete_plan(saved['plan']['id'])
    assert first.restore_saved_application_state()['plans'] == []
    assert first.restore_saved_application_state()['coursework'] == [item]

def test_stale_transaction_cannot_overwrite_another_save(remote):
    first, second = repository(), repository()
    first.initialize()
    with pytest.raises(RepositoryError, match='Someone else saved'):
        with first.transaction() as transaction:
            transaction.insert(coursework('Stale'), 'manual')
            second.store_coursework('CREATE', coursework('Winner'))
    assert [row['item_name'] for row in first.restore_saved_application_state()['coursework']] == ['Winner']

def test_exception_rolls_back_without_remote_write(remote):
    repo = repository()
    repo.initialize()
    before = deepcopy(remote.row)
    with pytest.raises(ValueError):
        with repo.transaction() as transaction:
            transaction.insert(coursework(), 'manual')
            raise ValueError('abort')
    assert remote.row == before
    assert 'PATCH' not in remote.calls

def test_failed_upload_never_reports_success_or_leaks_credentials(remote):
    repo = repository()
    repo.initialize()
    before = deepcopy(remote.row)
    remote.fail_before_patch = True
    with pytest.raises(RepositoryError, match='could not be confirmed') as error:
        repo.store_coursework('CREATE', coursework())
    assert 'secret' not in str(error.value)
    assert remote.row == before
    assert repo.restore_saved_application_state()['coursework'] == []

def test_timeout_after_commit_is_confirmed_without_duplicate_write(remote):
    repo = repository()
    repo.initialize()
    remote.timeout_after_patch = True
    saved = repo.store_coursework('CREATE', coursework())
    assert repo.restore_saved_application_state()['coursework'] == [saved]
    assert remote.calls.count('PATCH') == 1

def test_bootstrap_race_preserves_winner(remote):
    original = repository()
    original.initialize()
    original.store_coursework('CREATE', coursework('Existing'))
    winner = deepcopy(remote.row)
    remote.row = None
    remote.bootstrap_winner = winner
    newcomer = repository()
    newcomer.initialize()
    assert remote.row == winner
    assert newcomer.restore_saved_application_state()['coursework'][0]['item_name'] == 'Existing'

def test_migration_preserves_ids_and_data(remote):
    connection = sqlite3.connect(':memory:')
    for statement in SCHEMA:
        connection.execute(statement)
    connection.execute("INSERT INTO coursework(id,course,item_name,due_date,source) VALUES(7,'C','Assignment','2026-11-01','manual')")
    connection.execute("INSERT INTO plans(id,coursework_id,name) VALUES(11,7,'Plan')")
    connection.execute('PRAGMA user_version=1')
    connection.commit()
    remote.row = {'id': 'shared-demo', 'version': 4,
        'sqlite_base64': base64.b64encode(connection.serialize()).decode(), 'mutation_id': None}
    connection.close()
    repo = repository()
    repo.initialize()
    state = repo.restore_saved_application_state()
    assert state['coursework'][0]['id'] == 7
    assert state['coursework'][0]['start_time'] is None
    assert state['plans'][0]['id'] == 11
    assert remote.row['version'] == 5
    with repo._read_snapshot() as restored:
        assert restored.execute('PRAGMA user_version').fetchone()[0] == SCHEMA_VERSION

def test_invalid_child_rolls_back_whole_aggregate(remote):
    repo = repository()
    repo.initialize()
    item = repo.store_coursework('CREATE', coursework())
    before = deepcopy(remote.row)
    with pytest.raises(RepositoryError, match='foreign tasks ID'):
        repo.store_plan_data({'coursework_id': item['id'], 'name': 'Bad'}, tasks=[{'id': 999}])
    assert remote.row == before
    assert repo.restore_saved_application_state()['plans'] == []

@pytest.mark.parametrize('contents', ['invalid-base64!', base64.b64encode(b'not a database').decode()])
def test_corruption_fails_closed(remote, contents):
    remote.row = {'id': 'shared-demo', 'version': 1, 'sqlite_base64': contents, 'mutation_id': None}
    before = deepcopy(remote.row)
    with pytest.raises(RepositoryError, match='invalid database'):
        repository().initialize()
    assert remote.row == before
    assert remote.calls == ['GET']

def test_bad_configuration_and_read_outage_fail_closed(remote, monkeypatch):
    with pytest.raises(RepositoryError, match='configuration'):
        CloudAcademicRepository('https://example.supabase.co', '', 'token')
    with pytest.raises(RepositoryError, match='HTTPS'):
        CloudAcademicRepository('http://example.supabase.co', 'key', 'token')
    def outage(*args, **kwargs):
        raise requests.Timeout()
    monkeypatch.setattr('folio.cloud_storage.requests.request', outage)
    with pytest.raises(RepositoryError, match='unavailable'):
        repository().initialize()
    assert remote.calls == []
