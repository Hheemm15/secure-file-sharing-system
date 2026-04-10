from encryption import decrypt_file, encrypt_file


def test_encryption_round_trip():
    data = b"secret"

    encrypted = encrypt_file(data)
    decrypted = decrypt_file(encrypted)

    assert encrypted != data
    assert decrypted == data
