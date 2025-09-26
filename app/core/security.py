# Fichier: app/core/security.py

from cryptography.fernet import Fernet
from .config import settings

# Initialise Fernet avec la clé de la configuration
cipher_suite = Fernet(settings.FERNET_KEY.encode())

def encrypt_value(value: str) -> str:
    """Chiffre une valeur string."""
    return cipher_suite.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value: str) -> str:
    """Déchiffre une valeur."""
    return cipher_suite.decrypt(encrypted_value.encode()).decode()