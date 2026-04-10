import auth


def test_register_hashes_password(client, fake_db):
    response = client.post('/register', data={
        'username': 'testuser1',
        'password': '123'
    })

    assert response.status_code == 302
    assert fake_db.cursor.users['testuser1'] == auth.hash_password('123')


def test_login_migrates_legacy_plaintext_password(client, fake_db):
    fake_db.add_user('legacy_user', '123')

    response = client.post('/login', data={
        'username': 'legacy_user',
        'password': '123'
    })

    assert response.status_code == 302
    assert fake_db.cursor.users['legacy_user'] == auth.hash_password('123')
