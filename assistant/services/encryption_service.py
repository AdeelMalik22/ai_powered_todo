"""
Encryption/Decryption service for vault data using Fernet symmetric encryption.
"""

import os
from cryptography.fernet import Fernet
import base64
import hashlib


class EncryptionService:
    def __init__(self, encryption_key=None):
        """
        Initialize the encryption service with a Fernet key.

        If no key is provided, it will derive one from environment variable or create a default.
        """
        if encryption_key is None:
            encryption_key = os.environ.get('ENCRYPTION_KEY', 'default-dev-key')

        # Derive a valid Fernet key from the provided string
        self.key = self._derive_key(encryption_key)
        self.cipher = Fernet(self.key)

    @staticmethod
    def _derive_key(key_string: str) -> bytes:
        """
        Derive a valid Fernet key from a string using SHA-256.
        Fernet requires a 32-byte key encoded in base64.
        """
        # Hash the input string to get 32 bytes
        hash_object = hashlib.sha256(key_string.encode())
        hash_bytes = hash_object.digest()
        # Encode to base64 to get valid Fernet key
        key = base64.urlsafe_b64encode(hash_bytes)
        return key

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext and return base64-encoded ciphertext string.
        """
        ciphertext = self.cipher.encrypt(plaintext.encode())
        return ciphertext.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt base64-encoded ciphertext and return plaintext string.
        """
        try:
            plaintext = self.cipher.decrypt(ciphertext.encode())
            return plaintext.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")


def get_encryption_service():
    """Factory function to get encryption service instance."""
    return EncryptionService()

