
import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def build_secret_key(secret):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt="",
        iterations=100000,
        backend=default_backend()
    )

    return base64.urlsafe_b64encode(kdf.derive(bytes(secret)))


def encrypt(message, key):
    if key == None:
        return message
    else:
        f = Fernet(key)
        return f.encrypt(bytes(message))


def decrypt(message, key):
    if key == None:
        return message
    else:
        f = Fernet(key)
        return f.decrypt(bytes(message))


def hash(data):
    digest = hashes.Hash(hashes.SHA1(), backend=default_backend())
    digest.update(data)

    return digest.finalize()


def verify(data, data_hash):
    return hash(data) == data_hash
