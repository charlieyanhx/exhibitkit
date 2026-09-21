"""Font resolution: first installed family from a candidate list, via fontconfig; the last candidate
is the guaranteed fallback (a TeX Gyre face shipped with TeX Live) and is returned when nothing is
installed or fc-list is unavailable."""
from __future__ import annotations

import shutil
import subprocess
from functools import lru_cache


@lru_cache(maxsize=1)
def installed_families() -> frozenset[str]:
    if not shutil.which("fc-list"):
        return frozenset()
    try:
        out = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True, timeout=20).stdout
    except (subprocess.SubprocessError, OSError):
        return frozenset()
    fams: set[str] = set()
    for line in out.splitlines():
        for fam in line.split(","):
            fam = fam.strip()
            if fam:
                fams.add(fam)
    return frozenset(fams)


def resolve(candidates: list[str]) -> str:
    """Return the first installed family; else the last candidate (the TeX Live fallback)."""
    if not candidates:
        raise ValueError("empty font candidate list")
    fams = installed_families()
    for c in candidates:
        if c in fams:
            return c
    return candidates[-1]
