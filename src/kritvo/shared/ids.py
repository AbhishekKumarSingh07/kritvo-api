"""UUIDv7 identifiers (LLD 3.2: "IDs are UUIDv7 generated in the application").

Python 3.13's standard library has no ``uuid.uuid7`` (added upstream only in 3.14), so
this is a small, dependency-free implementation of RFC 9562's layout: a 48-bit
millisecond timestamp, a 4-bit version, and 74 random bits. Sorting by id sorts by
creation time, which is why the LLD asks for v7 over the random v4 the rest of the
codebase has never needed to generate before now.
"""

import os
import time
from uuid import UUID


def uuid7() -> UUID:
    ms = time.time_ns() // 1_000_000
    raw = os.urandom(10)
    b = bytearray(16)
    b[0:6] = ms.to_bytes(6, "big")
    b[6] = 0x70 | (raw[0] & 0x0F)  # version 7
    b[7] = raw[1]
    b[8] = 0x80 | (raw[2] & 0x3F)  # variant 10
    b[9:16] = raw[3:10]
    return UUID(bytes=bytes(b))
