from encryption import encrypt_file


def test_invalid_secure_share(client):
    with client.session_transaction() as session:
        session['user'] = 'guest'

    response = client.get('/secure-share/invalid')

    assert b"Invalid link!" in response.data


def test_secure_share_grants_access_and_downloads_file(client, fake_db, workspace_tmpdir):
    owner_folder = workspace_tmpdir / "uploads" / "owner1"
    owner_folder.mkdir(parents=True)
    filepath = owner_folder / "file1_report.txt"
    filepath.write_bytes(encrypt_file(b"shared content"))

    fake_db.add_user('guest', 'guest-password')
    fake_db.add_file(
        file_id='file1',
        filename='report.txt',
        owner='owner1',
        filepath=str(filepath)
    )

    with client.session_transaction() as session:
        session['user'] = 'guest'

    response = client.get('/secure-share/file1')

    assert response.status_code == 200
    assert response.data == b"shared content"
    assert ('file1', 'guest') in fake_db.cursor.file_access


def test_shared_user_can_download_by_file_id(client, fake_db, workspace_tmpdir):
    owner_folder = workspace_tmpdir / "uploads" / "owner1"
    owner_folder.mkdir(parents=True)
    filepath = owner_folder / "file2_notes.txt"
    filepath.write_bytes(encrypt_file(b"download me"))

    fake_db.add_user('receiver', 'hashed')
    fake_db.add_file(
        file_id='file2',
        filename='notes.txt',
        owner='owner1',
        filepath=str(filepath)
    )
    fake_db.grant_access('file2', 'receiver')

    with client.session_transaction() as session:
        session['user'] = 'receiver'

    response = client.get('/download/file2')

    assert response.status_code == 200
    assert response.data == b"download me"
