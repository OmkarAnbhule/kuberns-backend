"""
Encryption utilities using django-encrypted-model-fields

TODO: Implement proper encryption/decryption helpers
- Load FIELD_ENCRYPTION_KEY from environment (see settings.py)
- Use encrypted_model_fields for model field encryption
- Consider AWS KMS integration for production
"""

import os
from django.conf import settings
from cryptography.fernet import Fernet


def encrypt_value(plain: str) -> str:
    """
    Encrypt a plain text value using the configured encryption key.
    
    Uses Fernet encryption with the key from settings.
    """
    try:
        f = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
        return f.encrypt(plain.encode()).decode()
    except Exception as e:
        # Fallback for development - don't use in production
        return f"encrypted_{plain}"


def decrypt_value(token: str) -> str:
    """
    Decrypt an encrypted token back to plain text.
    
    Uses Fernet decryption with the key from settings.
    """
    try:
        f = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
        return f.decrypt(token.encode()).decode()
    except Exception as e:
        # Fallback for development - don't use in production
        return token.replace("encrypted_", "")


def get_encryption_key() -> str:
    """
    Get the encryption key from environment variables.
    
    TODO: In production, consider using AWS KMS or similar key management service
    """
    return settings.FIELD_ENCRYPTION_KEY