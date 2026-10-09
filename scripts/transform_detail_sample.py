"""Offline pilot for four Wiki search-cache page views. Never fetches or publishes."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v1-93a6a8b8d40e754a"
CARD_FILE = ROOT / "site" / "data" / VERSION / "cards.json"
SOURCE_DIR = ROOT / "private" / "raw" / "detail-sample-20261009-cache"
OUTPUT = ROOT / "private" / "audits" / "detail-sample-20261009.json"
LINE = re.compile(r"^L(\d+): ?(.*)$")
MECHANIC = re.compile(r"\((Link|Plus|Change|GrowUp|Grow|Refrain|Reflain)\)", re.I)
BG = re.compile(r"BGCOLOR\([^)]*\):")
COLOR = re.compile(r"&color\([^)]*\)\{([^{}]*)\};")
NOBR = re.compile(r"&nobr\{([^{}]*)\};")
LINK = re.compile(r"\[\[((?:(?!\]\]).)*?)>[^\[\]]+\]\]")


def clean(value: str) -> str:
    value = BG.sub("", value)
    for _ in range(4):
        value = COLOR.sub(r"\1", value)
        value = NOBR.sub(r"\1", value)
        value = LINK.sub(r"\1", value)
    value = value.replace("&br;", " ").replace("~", "", 1)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def row(text: str) -> list[str]:
    return text.strip().split("|")[1:-1]


def parse_cached(path: Path) -> tuple[str, dict[int, str], str, str]:
    raw = path.read_bytes()
    wrapper = raw.decode("utf-8-sig")
    match = re.search(r"\((https://wikiwiki\.jp/shinycolors/[^)]+)\)", wrapper.splitlines()[0])
    if not match:
        raise ValueError(f"Missing Wiki URL: {path}")
    url = match.group(1)
    crawl = re.search(r"Crawled: ([^;]+);", wrapper)
    lines = {}
    for entry in wrapper.splitlines():
        found = LINE.match(entry)
        if found:
            number = int(found.group(1))
            if number in lines:
                raise ValueError(f"Duplicate source line {number}: {path}")
            lines[number] = found.group(2).strip()
    if not lines or sorted(lines) != list(range(max(lines) + 1)):
        raise ValueError(f"Partial search-cache page view: {path}")
    return url, lines, hashlib.sha256(raw).hexdigest(), crawl.group(1) if crawl else "unknown"


def canonical(url: str) -> str:
    parsed = urlsplit(url)
    return parsed.netloc.lower() + unquote(parsed.path)


def section(lines: dict[int, str], heading: str, level: int = 1) -> list[tuple[int, str]]:
    prefix = "*" * level
    starts = [i for i, text in lines.items() if text.startswith(prefix + heading + " ")]
    if len(starts) != 1:
        raise ValueError(f"Expected one {heading} section, found {len(starts)}")
    start = starts[0]
    stop = next((i for i in range(start + 1, max(lines) + 1)
                 if lines[i].startswith("*") and not lines[i].startswith("*" * (level + 1))), max(lines) + 1)
    return [(i, lines[i]) for i in range(start + 1, stop)]


def mechanics(effect: str) -> list[str]:
    aliases = {"growup": "grow", "reflain": "refrain"}
    return sorted({aliases.get(m.group(1).lower(), m.group(1).lower()) for m in MECHANIC.finditer(effect)})


def classify(effect: str) -> str:
    if "BGCOLOR(gainsboro)" in effect:
        return "panel_live"
    plain = clean(effect)
    if "[コスト:" in plain:
        return "quick_skill"
    if "(アビリティ)" in plain:
        return "unique_ability"
    if "上限+" in plain:
        return "cap_increase"
    if "[条件:" in plain and "[確率:" in plain:
        return "panel_passive"
    return "unclassified"


def panel_nodes(rows: list[tuple[int, str]]) -> list[dict]:
    result = []
    for at, (number, text) in enumerate(rows[:-1]):
        found = re.match(r"^\|~(\d+)\|", text)
        if not found:
            continue
        next_number, next_text = rows[at + 1]
        if not next_text.startswith("|~|"):
            raise ValueError(f"No paired effect row after source line {number}")
        names, effects = row(text), row(next_text)
        if len(names) != len(effects):
            raise ValueError(f"Unequal panel widths at source line {number}")
        for column in range(1, len(names)):
            name, effect = names[column].strip(), effects[column].strip()
            if not name or name in (">", "~") or name.endswith(":"):
                continue
            if not effect or effect in (">", "~"):
                raise ValueError(f"Missing panel effect at source line {number} column {column}")
            kind = classify(effect)
            record = {
                "kind": kind, "name": clean(name), "sp": int(found.group(1)),
                "unlock_star": int(m.group(1)) if (m := re.search(r"☆(\d+)", name)) else None,
                "panel_column": column, "source_lines": [number, next_number],
                "effect_private": clean(effect), "mechanics": mechanics(effect) if kind == "panel_live" else [],
            }
            if kind == "cap_increase":
                match = re.search(r"上限\+(\d+)", record["effect_private"])
                record["cap_delta"] = int(match.group(1)) if match else None
            if kind == "quick_skill":
                match = re.search(r"\[コスト:(\d+)\]", record["effect_private"])
                record["energy_cost"] = int(match.group(1)) if match else None
            result.append(record)
    return result


def mb_skills(rows: list[tuple[int, str]]) -> list[dict]:
    indices = [i for i, (_, text) in enumerate(rows) if "メモリーブースト" in text and text.startswith("|")]
    if not indices:
        return []
    if len(indices) != 1:
        raise ValueError("Multiple MB tables")
    i = indices[0]
    header_number, header_text = rows[i + 2]
    effect_number, effect_text = rows[i + 3]
    names, effects = row(header_text), row(effect_text)
    if len(names) != len(effects):
        raise ValueError("MB table width mismatch")
    result = []
    for name, effect in zip(names, effects):
        if "[MB]" not in name:
            continue
        stage = re.search(r"\((\d+)/(\d+)\)", name)
        if not stage or "BGCOLOR(gainsboro)" not in effect:
            raise ValueError("MB row structure changed")
        result.append({
            "kind": "mb_live", "name": clean(name), "mb_stage": int(stage.group(1)),
            "mb_total_stages": int(stage.group(2)), "effect_private": clean(effect),
            "mechanics": mechanics(effect), "source_lines": [header_number, effect_number],
            "base_panel_link": "needs_review",
        })
    return result


def memory_appeals(rows: list[tuple[int, str]]) -> list[dict]:
    result = []
    for number, text in rows:
        if "思い出アピール[Lv" not in text or not text.startswith("|"):
            continue
        cells = row(text)
        match = re.search(r"思い出アピール\[Lv(\d+)\]", cells[1])
        if not match:
            raise ValueError(f"Unparsed memory appeal at line {number}")
        result.append({
            "kind": "memory_appeal", "level": int(match.group(1)), "name": clean(cells[0]),
            "effect_private": clean(cells[1]),
            "link_appeal_private": clean(cells[2]) if len(cells) > 2 and cells[2] != "~" else None,
            "charge_appeal_private": clean(cells[4]) if len(cells) > 4 and cells[4] not in ("", "~") else None,
            "source_lines": [number],
        })
    return result


def s_traits(lines: dict[int, str]) -> dict:
    values = {}
    for text in lines.values():
        if not text.startswith("|~"):
            continue
        cells = row(text)
        if cells[0] in ("~アイデア", "~ひらめき", "~楽曲熟練度"):
            values[cells[0][1:]] = [clean(x) for x in cells[1:] if x.strip() not in ("", ">", "~")]
    if not all(values.get(x) for x in ("アイデア", "ひらめき", "楽曲熟練度")):
        raise ValueError("Missing S traits")
    return {
        "idea": values["アイデア"][0], "inspiration": values["ひらめき"][0],
        "music_proficiencies": values["楽曲熟練度"],
    }


def s_max_status(rows: list[tuple[int, str]]) -> dict:
    candidates = []
    for number, text in rows:
        cells = row(text) if text.startswith("|") else []
        if len(cells) < 5:
            continue
        level = re.match(r"~(\d+)", cells[0])
        if level and all(re.fullmatch(r"\d+", v.strip()) for v in cells[1:5]):
            candidates.append({
                "level": int(level.group(1)),
                "limit_break": int(m.group(1)) if (m := re.search(r"☆(\d+)", cells[0])) else None,
                "vocal": int(cells[1]), "dance": int(cells[2]),
                "visual": int(cells[3]), "mental": int(cells[4]), "source_lines": [number],
            })
    if not candidates or len({c["level"] for c in candidates}) != len(candidates):
        raise ValueError("Missing or duplicate S status levels")
    return max(candidates, key=lambda x: x["level"])


def possessed_live(rows: list[tuple[int, str]]) -> list[dict]:
    result = []
    for number, text in rows:
        cells = row(text) if text.startswith("|") else []
        if len(cells) != 3 or not cells[0].strip().startswith("BGCOLOR("):
            continue
        level = clean(cells[2])
        if not (level == "初期" or level.isdecimal()):
            continue
        result.append({
            "kind": "possessed_live", "name": clean(cells[0]), "effect_private": clean(cells[1]),
            "acquired_at_level": level, "mechanics": mechanics(cells[1]), "source_lines": [number],
        })
    return result


def support_skills(rows: list[tuple[int, str]]) -> list[dict]:
    headers = [(number, row(text)) for number, text in rows
               if text.startswith("|~|~|~1|")]
    if len(headers) != 1:
        raise ValueError("Missing support-skill level header")
    header_number, levels = headers[0]
    levels = [clean(x) for x in levels[2:]]
    result = []
    for number, text in rows:
        if number <= header_number or not text.startswith("|~"):
            continue
        cells = row(text)
        if len(cells) != len(levels) + 2:
            continue
        if not cells[0].startswith("~") or cells[0] in ("~", "~スキル名"):
            continue
        progression = [
            {"support_level": level, "skill_level": int(value.strip())}
            for level, value in zip(levels, cells[2:]) if value.strip().isdecimal()
        ]
        if not progression:
            raise ValueError(f"Support skill without levels at line {number}")
        result.append({
            "kind": "support_skill", "name": clean(cells[0]),
            "effect_private": clean(cells[1]), "progression": progression,
            "source_lines": [header_number, number],
        })
    return result


def build(source_dir: Path) -> dict:
    document = json.loads(CARD_FILE.read_text(encoding="utf-8"))
    cards = document["cards"] if isinstance(document, dict) else document
    by_url = {canonical(c["wiki_url"]): c for c in cards if c.get("wiki_url")}
    manifest_path = source_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {item["file"]: item for item in manifest["files"]}
    paths = sorted(source_dir.glob("*.txt"))
    if set(expected) != {path.name for path in paths}:
        raise ValueError("Input manifest/file list mismatch")
    result = []
    for path in paths:
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected[path.name]["sha256"]:
            raise ValueError(f"Input manifest hash mismatch: {path}")
        url, lines, sha, crawl = parse_cached(path)
        if canonical(url) != canonical(expected[path.name]["source_url"]):
            raise ValueError(f"Input manifest URL mismatch: {path}")
        card = by_url.get(canonical(url))
        if not card:
            raise ValueError(f"Source URL is not in base index: {url}")
        panel = section(lines, "スキルパネル")
        nodes = panel_nodes(panel)
        if any(node["kind"] == "unclassified" for node in nodes):
            raise ValueError(f"Unclassified panel node in {path}")
        record = {
            "card_id": card["card_id"], "card_kind": card["card_kind"],
            "card_title": card["card_title"], "wiki_url": card["wiki_url"],
            "source_kind": "web_search_cache_view", "cache_crawled": crawl,
            "source_sha256": sha, "panel_nodes": nodes,
            "coverage": {"skill_panel": "extracted", "review": "needs_review"},
        }
        if card["card_kind"] == "P":
            record["mb_live"] = mb_skills(panel)
            record["memory_appeals"] = memory_appeals(section(lines, "思い出アピール"))
            record["coverage"].update({
                "memory_boost": "extracted" if record["mb_live"] else "no_entry_confirmed",
                "memory_appeal": "extracted", "stage_skill": "not_collected",
                "aptitude": "not_collected",
            })
            ability = section(lines, "アビリティ") if any(
                text.startswith("*アビリティ ") for text in lines.values()) else []
            record["ability_section_private"] = [
                {"source_line": number, "values": [clean(x) for x in row(text)]}
                for number, text in ability if text.startswith("|")
            ]
            abilities = [n for n in nodes if n["kind"] == "unique_ability"]
            evidence = record.pop("ability_section_private")
            if len(abilities) != len(evidence):
                raise ValueError("Panel/ability-section count differs")
            for ability, source in zip(abilities, evidence):
                values = source["values"]
                if len(values) < 2 or ability["name"] != values[0] or (
                    ability["effect_private"].removeprefix("(アビリティ)").strip() != values[1]
                ):
                    raise ValueError("Panel/ability-section content differs")
                ability["source_lines"].append(source["source_line"])
                ability["second_section_confirmed"] = True
            record["coverage"]["unique_ability"] = (
                "extracted" if abilities else "no_entry_confirmed"
            )
        else:
            record["traits"] = s_traits(lines)
            record["max_status"] = s_max_status(section(lines, "ステータス"))
            record["possessed_live"] = possessed_live(section(lines, "ライブスキル", 2))
            record["support_skills"] = support_skills(section(lines, "サポートスキル", 2))
            record["coverage"].update({
                "traits": "extracted", "max_status": "extracted",
                "possessed_live": "extracted", "support_skills": "extracted",
                "quick_skill": "extracted" if any(n["kind"] == "quick_skill" for n in nodes)
                              else "no_entry_confirmed",
                "fight_skill": "not_collected",
            })
        result.append(record)
    if len(result) != 4 or [x["card_kind"] for x in result].count("P") != 2:
        raise ValueError("Pilot must contain two P and two S cards")
    output = {
        "pilot_schema": "0.1", "base_dataset_version": VERSION,
        "input_kind": "Wiki search-service cached page views, not live HTML",
        "input_captured_at_utc": manifest["captured_at_utc"],
        "cards": result,
    }
    stable = json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    output["content_hash"] = hashlib.sha256(stable.encode("utf-8")).hexdigest()
    output["transformed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to((ROOT / "private").resolve()):
        raise ValueError("Private audit output must stay under private/")
    document = build(args.source_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    for card in document["cards"]:
        from collections import Counter
        kinds = Counter(node["kind"] for node in card["panel_nodes"])
        print(json.dumps({
            "card_id": card["card_id"], "kind": card["card_kind"], "panel": kinds,
            "mb": len(card.get("mb_live", [])), "memory": len(card.get("memory_appeals", [])),
            "possessed": len(card.get("possessed_live", [])),
            "support": len(card.get("support_skills", [])),
            "max_level": card.get("max_status", {}).get("level"),
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
