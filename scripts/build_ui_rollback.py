"""Create a verified UI rollback candidate without changing the active site."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from check_site import check

ROOT = Path(__file__).resolve().parents[1]
UI_FILES = ("index.html", "style.css", "app.mjs", "search.mjs")
TAG_RE = re.compile(r"ui-v[0-9]+(?:-[A-Za-z0-9]+)*\Z")


def git(*args):
    return subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def build_candidate(ref, source, output):
    if not TAG_RE.fullmatch(ref):
        raise ValueError("UI ref must be a versioned ui-v* tag")
    git("rev-parse", "--verify", f"refs/tags/{ref}^{{commit}}")
    source = Path(source).resolve()
    output = Path(output).resolve()
    if not source.is_relative_to(ROOT) or not output.is_relative_to(ROOT):
        raise ValueError("source and output must stay inside the project")
    if not source.is_dir() or not (source / "data/latest.json").is_file():
        raise ValueError("source is not a site directory")
    if output.exists() or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("output must be a new directory separate from source")
    version = json.loads((source / "data/latest.json").read_text(encoding="utf-8"))["dataset_version"]
    tagged_version = json.loads(git("show", f"refs/tags/{ref}:site/data/latest.json"))["dataset_version"]
    # The published site files are stored byte-for-byte; web/ is normalized by Git.
    assets = {name: git("show", f"refs/tags/{ref}:site/{name}") for name in UI_FILES}
    old = f"window.DATA_VERSION='{tagged_version}'".encode("ascii")
    new = f"window.DATA_VERSION='{version}'".encode("ascii")
    if assets["index.html"].count(old) != 1:
        raise ValueError("tagged site has an unexpected data version marker")
    assets["index.html"] = assets["index.html"].replace(old, new)
    shutil.copytree(source, output)
    for name, content in assets.items():
        (output / name).write_bytes(content)
    check(output)
    return {"ui_ref": ref, "dataset_version": version, "output": str(output)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", required=True, help="versioned UI tag, such as ui-v1-20261008")
    parser.add_argument("--source", default="site", help="validated current site")
    parser.add_argument("--output", required=True, help="new candidate directory inside this project")
    args = parser.parse_args()
    print(json.dumps(build_candidate(args.ref, args.source, args.output), ensure_ascii=False))