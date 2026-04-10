from app import app
import pytest

def test_invalid_share(client):
    response = client.get('/share/invalid')
    assert b"Invalid" in response.data