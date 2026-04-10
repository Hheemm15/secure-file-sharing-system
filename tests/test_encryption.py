from encryption import encrypt_file, decrypt_file

def test_encryption():
    data = b"secret"

    encrypted = encrypt_file(data)
    decrypted = decrypt_file(encrypted)

    assert decrypted == data