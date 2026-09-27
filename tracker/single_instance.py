"""Process-singleton guard via a Windows named mutex (fcntl on POSIX).

File-based locks proved unreliable here: the tooling retries launches under
two different interpreters and a truncating re-open can clobber a held
byte-range lock. A named mutex is a kernel object -- cross-process,
cross-interpreter, and immune to filesystem races.
"""
from __future__ import annotations

import sys

_holder = None  # keep the handle/reference alive for the process lifetime


def acquire(name: str) -> bool:
    """Return True if this process now owns the singleton ``name``."""
    global _holder
    if sys.platform == "win32":
        import ctypes

        handle = ctypes.windll.kernel32.CreateMutexW(None, False, name)
        if not handle:
            return False
        # WAIT_OBJECT_0 = 0; WAIT_ABANDONED = 0x80 also means we own it now
        # (previous owner died without releasing), which is fine for us.
        if ctypes.windll.kernel32.WaitForSingleObject(handle, 0) in (0, 0x80):
            _holder = handle
            return True
        return False
    import fcntl

    fh = open(f"/tmp/{name}.lock", "w")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    _holder = fh
    return True
