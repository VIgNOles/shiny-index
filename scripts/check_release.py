"""Validate committed UI bytes and preserve the exact tree tested before deployment."""
import argparse
import hashlib
import json
import sys
import tarfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.check_site import check
from scripts.refresh_ui_assets import WEB_ROOT, render_ui_assets


def check_ui_assets(root: Path, source: Path = WEB_ROOT) -> None:
    for name, expected in render_ui_assets(root, source).items():
        path = root / name
        if not path.is_file() or path.read_bytes() != expected:
            raise ValueError(f"UI asset differs from web source: {name}; refresh the candidate before review")


def file_manifest(root: Path) -> dict:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("site root is missing or a symlink")
    paths = sorted(root.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise ValueError("symlink in site")
    return {"schema_version": 1, "files": {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths if path.is_file()
    }}


def compare_manifest(current: dict, expected: dict, *, context: str = "Release tree changed during verification") -> None:
    if current != expected:
        before, after = expected.get("files", {}), current["files"]
        changes = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
        raise ValueError(context + ": " + ", ".join(changes[:5]))


def check_artifact(path: Path, expected: dict) -> None:
    """Compare the actual Pages archive, including its complete file membership."""
    files = {}
    with tarfile.open(path) as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts:
                raise ValueError("Unsafe path in Pages artifact")
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError("Non-regular file in Pages artifact")
            key = name.as_posix()
            if key in files:
                raise ValueError("Duplicate file in Pages artifact")
            with archive.extractfile(member) as stream:
                files[key] = hashlib.sha256(stream.read()).hexdigest()
    compare_manifest({"schema_version": 1, "files": files}, expected,
                     context="Pages artifact differs from tested release")


def check_release(root: Path, source: Path = WEB_ROOT) -> dict:
    check(root)
    check_ui_assets(root, source)
    return file_manifest(root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--record", type=Path, help="Record the tested tree outside the site before running tests")
    mode.add_argument("--compare", type=Path, help="Require the same exact tree after running tests")
    parser.add_argument("--artifact", type=Path, help="Require the actual Pages tar archive to match the verified tree")
    args = parser.parse_args()
    if args.record and args.record.resolve().is_relative_to(args.site.resolve()):
        parser.error("Save the verification manifest outside the site")
    if args.compare:
        # Identical bytes retain the successful initial structural/data validation.
        check_ui_assets(args.site)
        manifest = file_manifest(args.site)
        compare_manifest(manifest, json.loads(args.compare.read_text(encoding="utf-8")))
    else:
        manifest = check_release(args.site)
    if args.artifact:
        check_artifact(args.artifact, manifest)
    if args.record:
        args.record.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Verified exact release tree: {len(manifest['files'])} files")
