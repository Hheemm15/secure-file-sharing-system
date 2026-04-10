import io
from app import app
import pytest

def test_upload(client):
    client.post('/login', data={
        'username': 'testuser1',
        'password': '123'
    })

    data = {
        'file': (io.BytesIO(b"hello"), 'test.txt')
    }

    response = client.post('/upload', data=data, content_type='multipart/form-data')

    assert response.status_code == 302