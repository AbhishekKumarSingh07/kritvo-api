"""Access-token signing keys (LLD 12.2).

Lives in ``core``, not in ``identity``, because ``core.deps`` has to decode tokens on
every authenticated request, and core may never import a feature module — so the
encode/decode machinery both sides share has to sit below that boundary, even though
using it to actually log someone in is identity's job.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ACCESS_TOKEN_ALGORITHM = "EdDSA"  # noqa: S105 — a JWT `alg` name, not a credential
ACCESS_TOKEN_TTL = timedelta(minutes=15)


class KeyRing:
    """Loads every ``<kid>.pem`` Ed25519 private key in a directory.

    ``active_kid`` signs new access tokens; every loaded key still verifies, so a
    just-retired kid keeps validating tokens issued under it until they expire — the
    "two keys active during rotation" requirement.
    """

    def __init__(self, keys: dict[str, Ed25519PrivateKey], active_kid: str) -> None:
        if active_kid not in keys:
            raise ValueError(f"active kid {active_kid!r} not found among loaded signing keys")
        self._keys = keys
        self.active_kid = active_kid

    @classmethod
    def generate_ephemeral(cls, kid: str) -> "KeyRing":
        """An in-memory key, generated fresh each process start.

        Local/dev/test convenience only, so the app and its tests can start with no
        manual setup step and no key material ever touching disk. Anywhere a signing
        key needs to survive a restart, put a real ``<kid>.pem`` in the configured
        directory instead — ``from_directory`` is used whenever one exists.
        """
        return cls({kid: Ed25519PrivateKey.generate()}, kid)

    @classmethod
    def from_directory(cls, directory: Path, active_kid: str) -> "KeyRing":
        keys: dict[str, Ed25519PrivateKey] = {}
        for path in sorted(directory.glob("*.pem")):
            private_key = serialization.load_pem_private_key(path.read_bytes(), password=None)
            if not isinstance(private_key, Ed25519PrivateKey):
                raise ValueError(f"{path} is not an Ed25519 private key")
            keys[path.stem] = private_key
        return cls(keys, active_kid)

    def encode(self, claims: dict[str, Any], *, ttl: timedelta = ACCESS_TOKEN_TTL) -> str:
        now = datetime.now(UTC)
        payload = {**claims, "iat": now, "exp": now + ttl}
        return jwt.encode(
            payload,
            self._keys[self.active_kid],
            algorithm=ACCESS_TOKEN_ALGORITHM,
            headers={"kid": self.active_kid},
        )

    def decode(self, token: str) -> dict[str, Any]:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not isinstance(kid, str) or kid not in self._keys:
            raise jwt.InvalidTokenError(f"unknown signing key id {kid!r}")
        public_key = self._keys[kid].public_key()
        decoded: dict[str, Any] = jwt.decode(token, public_key, algorithms=[ACCESS_TOKEN_ALGORITHM])
        return decoded
