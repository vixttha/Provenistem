"""Prospective notice verification; scope is defined by PROVENISTEM-NOTICE.md.

Only the original licensable expression in this new module is proposed for
PolyForm Strict 1.0.0. Review branches are not authorized distributions.
No permission enforcement, source authentication or installation is implied.
"""
from hashlib import sha256


def verify_notices(source, expected):
    """Compare exact local notice bytes to the selected revision's expected hashes."""
    for name, digest in sorted(expected.items()):
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"required license/notice missing or unsafe: {name}")
        if sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"license/notice bytes do not match selected revision: {name}")
