from app import app
import pytest


def test_register(client):
    response = client.post('/register', data={
        'username': 'testuser1',
        'password': '123'
    })
    assert response.status_code == 302

def test_login(client):
    response = client.post('/login', data={
        'username': 'testuser1',
        'password': '123'
    })
    assert response.status_code == 302