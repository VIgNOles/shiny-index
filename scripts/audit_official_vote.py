"""Offline comparison of the 2026 official P-SSR vote list and a release."""
import argparse
import json
import unicodedata
from collections import Counter
from pathlib import Path


def key(name, title):
    def norm(value):
        return "".join(c for c in unicodedata.normalize("NFKC", value or "") if not c.isspace())
    return norm(name), norm(title)


def audit(official, release):
    if not isinstance(official, list) or not official:
        raise ValueError("empty official list")
    if not isinstance(release.get("cards"), list) or not release["cards"]:
        raise ValueError("empty release")
    vote = Counter(key(row["idol_name"], row["commu_title"]) for row in official)
    cards = [row for row in release["cards"] if row["card_kind"] == "P" and row["rarity"] == "SSR"]
    local = Counter(key(row["idol_name"], row["card_title"]) for row in cards)
    return {
        "official_rows": len(official),
        "official_unique_keys": len(vote),
        "official_duplicate_keys": [list(k) for k, n in vote.items() if n > 1],
        "local_p_ssr_rows": len(cards),
        "local_unique_keys": len(local),
        "local_duplicate_keys": [list(k) for k, n in local.items() if n > 1],
        "official_not_in_local": [list(k) for k in sorted(vote.keys() - local.keys())],
        "local_not_in_official": [list(k) for k in sorted(local.keys() - vote.keys())],
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("official_json", type=Path)
    p.add_argument("release_json", type=Path)
    p.add_argument("output_json", type=Path)
    args = p.parse_args()
    official = json.loads(args.official_json.read_text(encoding="utf-8-sig"))
    release = json.loads(args.release_json.read_text(encoding="utf-8-sig"))
    result = audit(official, release)
    if args.output_json.exists():
        old = json.loads(args.output_json.read_text(encoding="utf-8-sig"))
        if old != result:
            raise FileExistsError("existing audit differs")
    else:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
