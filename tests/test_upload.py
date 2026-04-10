import io
from pathlib import Path

from encryption import decrypt_file


def test_upload_encrypts_file_before_saving(client, fake_db):
    fake_db.add_user('testuser1', 'hashed')

    with client.session_transaction() as session:
        session['user'] = 'testuser1'

    response = client.post('/upload', data={
        'file': (io.BytesIO(b"hello"), 'test.txt')
    }, content_type='multipart/form-data')

    assert response.status_code == 302
    assert len(fake_db.cursor.files) == 1

    stored_file = next(iter(fake_db.cursor.files.values()))
    stored_path = Path(stored_file['filepath'])
    stored_bytes = stored_path.read_bytes()

    assert stored_bytes != b"hello"
    assert decrypt_file(stored_bytes) == b"hello"
