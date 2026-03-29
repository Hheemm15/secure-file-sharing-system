from cryptography.fernet import Fernet

key = b'J12CIlFHNTh2cJwQ3Og6Ou-f4sAC0QGhekYRsp3KRv4='

cipher = Fernet(key)

def encrypt_file(data):
    return cipher.encrypt(data)

def decrypt_file(data):
    return cipher.decrypt(data)