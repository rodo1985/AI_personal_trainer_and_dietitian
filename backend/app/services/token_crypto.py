"""Token encryption utilities for Strava OAuth credentials."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet


class TokenCrypto:
    """Encrypt and decrypt token values stored in SQLite.

    Parameters:
        secret_material: Raw secret string used to derive the encryption key.

    Returns:
        TokenCrypto: Instance ready to encrypt and decrypt token strings.

    Raises:
        ValueError: Raised if `secret_material` is blank.

    Example:
        >>> crypto = TokenCrypto("local-dev-secret")
        >>> token = crypto.encrypt("abc")
        >>> crypto.decrypt(token)
        'abc'
    """

    def __init__(self, secret_material: str) -> None:
        """Initialize the crypto helper with deterministic key derivation.

        Parameters:
            secret_material: Input string used to derive a stable Fernet key.

        Returns:
            None.

        Raises:
            ValueError: Raised when secret material is empty.

        Example:
            >>> TokenCrypto("my-secret")
            <...TokenCrypto object ...>
        """

        if not secret_material:
            raise ValueError("A non-empty secret is required for token encryption.")

        self._fernet = Fernet(self._derive_fernet_key(secret_material))

    @staticmethod
    def _derive_fernet_key(secret_material: str) -> bytes:
        """Derive a Fernet-compatible key from arbitrary secret material.

        Parameters:
            secret_material: Input secret string from environment configuration.

        Returns:
            bytes: URL-safe base64 key bytes accepted by `cryptography.Fernet`.

        Raises:
            None.

        Example:
            >>> isinstance(TokenCrypto._derive_fernet_key("x"), bytes)
            True
        """

        digest = hashlib.sha256(secret_material.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    def encrypt(self, value: str) -> str:
        """Encrypt a plain-text token value.

        Parameters:
            value: Plain-text token string.

        Returns:
            str: Encrypted token suitable for database storage.

        Raises:
            cryptography.fernet.InvalidToken: Not expected during encryption.

        Example:
            >>> crypto = TokenCrypto("secret")
            >>> isinstance(crypto.encrypt("token"), str)
            True
        """

        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        """Decrypt a stored token value.

        Parameters:
            value: Encrypted token string from database storage.

        Returns:
            str: Decrypted plain-text token.

        Raises:
            cryptography.fernet.InvalidToken: Raised when ciphertext is corrupted.

        Example:
            >>> crypto = TokenCrypto("secret")
            >>> encrypted = crypto.encrypt("token")
            >>> crypto.decrypt(encrypted)
            'token'
        """

        return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
