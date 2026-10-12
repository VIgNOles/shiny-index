"""Refresh the five UI assets without rebuilding or modifying immutable data bundles."""
import argparse
import json
import re
from pathlib import Path


UI_ASSETS = ("index.html", "app.mjs", "details.mjs", "search.mjs", "style.css")
WEB_ROOT = Path(__file__).resolve().parents[1] / "web"


def render_ui_assets(root: Path, source: Path = WEB_ROOT) -> dict[str, bytes]:
    """Render expected UI bytes in memory, without changing a release candidate."""
    base = json.loads((root / "data/latest.json").read_text(encoding="utf-8"))["dataset_version"]
    detail = json.loads((root / "details/latest.json").read_text(encoding="utf-8"))["detail_version"]
    if not re.fullmatch(r"v1-[0-9a-f]{16}", base) or not re.fullmatch(r"d1-[0-9a-f]{16}", detail):
        raise ValueError("Invalid data pointer")
    assets = {}
    for name in UI_ASSETS:
        content = (source / name).read_text(encoding="utf-8")
        content = content.replace("__VERSION__", base).replace("__DETAIL_VERSION__", detail)
        assets[name] = content.encode("utf-8")
    return assets


def refresh(root: Path) -> None:
    for name, content in render_ui_assets(root).items():
        (root / name).write_bytes(content)
    base = json.loads((root / "data/latest.json").read_text(encoding="utf-8"))["dataset_version"]
    detail = json.loads((root / "details/latest.json").read_text(encoding="utf-8"))["detail_version"]
    print(f"Refreshed UI only: {root}, {base}, {detail}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path)
    refresh(parser.parse_args().site)
