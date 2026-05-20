from cryptography.fernet import Fernet


def encrypt_value(value: str, key: str) -> str:
    """Encrypt a string value."""
    f = Fernet(key.encode())
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str, key: str) -> str:
    """Decrypt a string value."""
    f = Fernet(key.encode())
    return f.decrypt(encrypted.encode()).decode()
