"""Refresh the five UI assets without rebuilding or modifying immutable data bundles."""
import argparse
import json
import re
from pathlib import Path


def refresh(root: Path) -> None:
    base = json.loads((root / "data/latest.json").read_text(encoding="utf-8"))["dataset_version"]
    detail = json.loads((root / "details/latest.json").read_text(encoding="utf-8"))["detail_version"]
    if not re.fullmatch(r"v1-[0-9a-f]{16}", base) or not re.fullmatch(r"d1-[0-9a-f]{16}", detail):
        raise ValueError("Invalid data pointer")
    source = Path(__file__).resolve().parents[1] / "web"
    for name in ("index.html", "app.mjs", "details.mjs", "search.mjs", "style.css"):
        content = (source / name).read_text(encoding="utf-8")
        content = content.replace("__VERSION__", base).replace("__DETAIL_VERSION__", detail)
        (root / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"Refreshed UI only: {root}, {base}, {detail}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path)
    refresh(parser.parse_args().site)
