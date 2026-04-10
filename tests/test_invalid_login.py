def test_invalid_login(client):
    response = client.post('/login', data={
        'username': 'wrong',
        'password': 'wrong'
    }, follow_redirects=True)   

    assert b"Invalid" in response.data