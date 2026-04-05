from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("SECRET_KEY").encode()
cipher = Fernet(key)

def encrypt_file(data):
    return cipher.encrypt(data)

def decrypt_file(data):
    return cipher.decrypt(data)