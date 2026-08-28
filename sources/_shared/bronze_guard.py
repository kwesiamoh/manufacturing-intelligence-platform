"""Small immutable-Bronze helpers used by source downloaders.

Downloaders must never stream directly over a governed path. New content is
written to a sibling temporary file, checked, and installed only when the
canonical destination is absent. Existing complete artifact sets are reused;
partial sets and checksum conflicts fail explicitly.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import zipfile
from collections.abc import Iterable
from pathlib import Path


class ImmutableBronzeError(RuntimeError):
    """Raised when an acquisition would violate the immutable-Bronze boundary."""


def digest(path: Path, algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def reuse_complete_set_or_raise(
    paths: Iterable[Path],
    expected: dict[Path, tuple[str, str]] | None = None,
) -> bool:
    """Return True for a complete reusable set, False for an empty set.

    A partially populated set is ambiguous and therefore fails. Expected digest
    entries are `(algorithm, hex_digest)` pairs.
    """

    artifacts = [Path(path) for path in paths]
    present = [path for path in artifacts if path.is_file()]
    if not present:
        return False
    if len(present) != len(artifacts):
        missing = [str(path) for path in artifacts if not path.is_file()]
        raise ImmutableBronzeError(
            "Partial immutable Bronze set; refusing acquisition. Missing: "
            + ", ".join(missing)
        )

    expected = expected or {}
    for path in artifacts:
        if path in expected:
            algorithm, expected_hex = expected[path]
            observed = digest(path, algorithm)
            if observed.lower() != expected_hex.lower():
                raise ImmutableBronzeError(
                    f"Existing Bronze checksum conflict for {path}: "
                    f"expected {expected_hex}, observed {observed}"
                )
        print(f"REUSED immutable Bronze: {path} sha256={digest(path)}")
    return True


def install_chunks(
    target: Path,
    chunks: Iterable[bytes],
    *,
    expected_digest: str | None = None,
    algorithm: str = "sha256",
) -> tuple[str, bool]:
    """Install streamed bytes without overwriting a different target.

    Returns `(digest, reused_existing)`.
    """

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=target.name + ".", suffix=".incoming", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            for chunk in chunks:
                if chunk:
                    stream.write(chunk)

        observed = digest(temporary, algorithm)
        if expected_digest and observed.lower() != expected_digest.lower():
            raise ImmutableBronzeError(
                f"Downloaded checksum mismatch for {target}: expected "
                f"{expected_digest}, observed {observed}"
            )

        if target.exists():
            existing = digest(target, algorithm)
            if existing.lower() != observed.lower():
                raise ImmutableBronzeError(
                    f"Immutable Bronze conflict for {target}: existing {existing}, "
                    f"incoming {observed}; existing file was not overwritten"
                )
            temporary.unlink()
            print(f"REUSED identical immutable Bronze: {target} {algorithm}={observed}")
            return observed, True

        temporary.replace(target)
        print(f"INSTALLED immutable Bronze: {target} {algorithm}={observed}")
        return observed, False
    finally:
        temporary.unlink(missing_ok=True)


def install_bytes(
    target: Path,
    payload: bytes,
    *,
    expected_digest: str | None = None,
    algorithm: str = "sha256",
) -> tuple[str, bool]:
    return install_chunks(
        target,
        (payload,),
        expected_digest=expected_digest,
        algorithm=algorithm,
    )


def replace_derived_directory(staged: Path, target: Path) -> None:
    """Replace a derived directory as one unit, restoring the old one on error."""

    staged = Path(staged)
    target = Path(target)
    if not staged.is_dir():
        raise FileNotFoundError(f"Staged derived directory is missing: {staged}")
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = target.with_name(target.name + ".previous")
    if backup.exists():
        shutil.rmtree(backup)
    try:
        if target.exists():
            target.replace(backup)
        staged.replace(target)
    except Exception:
        if not target.exists() and backup.exists():
            backup.replace(target)
        raise
    else:
        if backup.exists():
            shutil.rmtree(backup)


def refresh_zip_extraction(
    archive: Path,
    target_directory: Path,
    *,
    required_suffix: str | None = None,
) -> list[Path]:
    """Replace a derived extraction directory from one ZIP as a clean unit."""

    archive = Path(archive)
    target_directory = Path(target_directory)
    target_directory.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=f".{target_directory.name}-extract-", dir=target_directory.parent
    ) as temporary_root:
        staged = Path(temporary_root) / target_directory.name
        staged.mkdir()
        staged_root = staged.resolve()
        with zipfile.ZipFile(archive) as source:
            for member in source.infolist():
                destination = (staged / member.filename).resolve()
                try:
                    destination.relative_to(staged_root)
                except ValueError as exc:
                    raise ImmutableBronzeError(
                        f"Unsafe ZIP member path in {archive}: {member.filename}"
                    ) from exc
            source.extractall(staged)

        files = [path for path in staged.rglob("*") if path.is_file()]
        if not files:
            raise ImmutableBronzeError(f"ZIP extraction produced no files: {archive}")
        if required_suffix and not any(path.suffix == required_suffix for path in files):
            raise ImmutableBronzeError(
                f"ZIP extraction from {archive} produced no {required_suffix} files"
            )

        replace_derived_directory(staged, target_directory)

    return [path for path in target_directory.rglob("*") if path.is_file()]
