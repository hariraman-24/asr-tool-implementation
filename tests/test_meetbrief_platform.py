import pytest
from app import app
from database.db import init_db, save_meeting_mom, get_all_meetings, delete_meeting

@pytest.fixture
def client():
    app.config['TESTING'] = True
    init_db()
    with app.test_client() as client:
        yield client

def test_index_page(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b'MeetBrief' in res.data
    assert b'Minutes of the Meeting (MoM)' in res.data

def test_save_and_retrieve_mom(client):
    res = client.post('/api/save-mom', data={
        'title': 'Sprint Planning Session',
        'mom_text': '[10:00 AM] Discussed sprint deliverables.\n[10:15 AM] Approved architecture.',
        'duration': '15:20'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'meeting_id' in data
    meeting_id = data['meeting_id']

    # Retrieve all
    res_list = client.get('/api/meetings')
    assert res_list.status_code == 200
    meetings = res_list.get_json()['meetings']
    assert any(m['id'] == meeting_id for m in meetings)

    # Download MoM TXT
    res_dl = client.get(f'/api/meeting/{meeting_id}/download')
    assert res_dl.status_code == 200
    assert b'MINUTES OF THE MEETING (MoM)' in res_dl.data
    assert b'Sprint Planning Session' in res_dl.data

    # Delete MoM
    res_del = client.delete(f'/api/meeting/{meeting_id}')
    assert res_del.status_code == 200
    assert res_del.get_json()['success'] is True

def test_save_mom_validation(client):
    # Empty text rejection
    res = client.post('/api/save-mom', data={
        'title': 'Empty Meeting',
        'mom_text': '',
        'duration': '00:00'
    })
    assert res.status_code == 400
    assert res.get_json()['success'] is False
