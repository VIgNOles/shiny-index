"""Replay one saved card HTML input. Never fetches, adopts, or publishes."""
import argparse
import json
import os
import tempfile
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.card_details import transform_run
from src.indexer import ROOT


def load_cards(root: Path, version: str) -> list[dict]:
    if not re.fullmatch(r"v1-[0-9a-f]{16}", version):
        raise ValueError("Invalid base dataset version")
    document = json.loads((root / "site/data" / version / "cards.json").read_text(encoding="utf-8"))
    return document["cards"]


def save_candidate(document: dict, output: Path, root=ROOT):
    if not output.resolve().is_relative_to((root / "private").resolve()):
        raise ValueError("Detail candidates must stay under private/")
    if output.exists():
        previous = json.loads(output.read_text(encoding="utf-8"))
        if previous != document:
            raise FileExistsError("Candidate differs; use a fresh output path")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    # Link the completely written file into place without replacing an existing path.
    # A process interruption can leave a .tmp file, but never a partial candidate.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                         prefix=output.name + ".", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("card_id")
    parser.add_argument("output", type=Path)
    parser.add_argument("--base-version", default="v1-93a6a8b8d40e754a")
    args = parser.parse_args()
    cards = [c for c in load_cards(ROOT, args.base_version) if c["card_id"] == args.card_id]
    if len(cards) != 1:
        raise ValueError("Expected one existing card_id")
    document = transform_run(args.source_dir, cards[0], args.base_version)
    save_candidate(document, args.output)
    from collections import Counter
    card = document["cards"][0]
    print(json.dumps({"card_id": card["card_id"], "card_kind": card["card_kind"],
                      "panel_counts": Counter(n["kind"] for n in card["panel_nodes"]),
                      "memory_levels": len(card["memory_appeals"]),
                      "content_hash": document["content_hash"], "review": "needs_review"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
