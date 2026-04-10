def test_invalid_login(client, fake_db):
    fake_db.add_user('valid_user', 'not-the-right-password-hash')

    response = client.post('/login', data={
        'username': 'valid_user',
        'password': 'wrong'
    }, follow_redirects=True)

    assert b"Invalid" in response.data
