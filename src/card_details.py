"""Offline extraction of saved Wiki HTML into private detail candidates."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup, Tag

MECHANIC = re.compile(r"[（(](Link|Plus|Change|GrowUp|Grow|Refrain|Reflain)[)）]", re.I)
HEADINGS = ("h2", "h3", "h4", "h5", "h6")


def wiki_key(url: str) -> str:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "wikiwiki.jp" or
            not unquote(parsed.path).startswith("/shinycolors/") or parsed.query or parsed.fragment):
        raise ValueError("Expected an individual Wiki URL without query or fragment")
    return unquote(parsed.path)


def text(tag: Tag) -> str:
    # Inline colour spans are fragments of words, while br elements separate lines.
    clone = BeautifulSoup(str(tag), "html.parser")
    for br in clone.find_all("br"):
        br.replace_with("\n")
    return re.sub(r"\s+", " ", clone.get_text()).strip()


def mechanics(effect: str) -> list[str]:
    aliases = {"growup": "grow", "reflain": "refrain"}
    return sorted({aliases.get(m[1].lower(), m[1].lower()) for m in MECHANIC.finditer(effect)})


@dataclass
class Cell:
    tag: Tag
    row: int
    column: int
    rowspan: int
    colspan: int

    @property
    def value(self):
        return text(self.tag)


def table_grid(table: Tag) -> list[list[Cell]]:
    """Expand spans, retaining the original cell for field-level evidence."""
    rows = [r for r in table.find_all("tr") if r.find_parent("table") is table]
    if not rows or len(rows) > 200:
        raise ValueError("Empty or oversized detail table")
    occupied = {}
    for r, tr in enumerate(rows):
        column = 0
        for tag in tr.find_all(["td", "th"], recursive=False):
            while (r, column) in occupied:
                column += 1
            try:
                rs, cs = int(tag.get("rowspan", 1)), int(tag.get("colspan", 1))
            except (TypeError, ValueError) as error:
                raise ValueError("Invalid table span") from error
            if rs < 1 or cs < 1 or r + rs > len(rows) or column + cs > 100:
                raise ValueError("Detail table span outside bounds")
            cell = Cell(tag, r, column, rs, cs)
            for rr in range(r, r + rs):
                for cc in range(column, column + cs):
                    if (rr, cc) in occupied:
                        raise ValueError("Overlapping detail table cells")
                    occupied[rr, cc] = cell
            column += cs
    if not occupied:
        raise ValueError("Detail table has no cells")
    width = max(c for _, c in occupied) + 1
    if any((r, c) not in occupied for r in range(len(rows)) for c in range(width)):
        raise ValueError("Ragged detail table")
    return [[occupied[r, c] for c in range(width)] for r in range(len(rows))]


def evidence(table_number: int, cell: Cell, anchor: str | None) -> dict:
    return {"table": table_number, "row": cell.row + 1, "column": cell.column + 1,
            "section_anchor": anchor}


def tables_in(content: Tag, heading: str, *, optional=False) -> list[tuple[int, Tag, str | None]]:
    matches = [h for h in content.find_all(HEADINGS) if text(h) == heading]
    if not matches and optional:
        return []
    if len(matches) != 1:
        raise ValueError(f"Expected one {heading} section, got {len(matches)}")
    start = matches[0]
    rank = int(start.name[1])
    anchor_node = start.select_one("a[name]")
    anchor = anchor_node.get("name") if anchor_node else start.get("id")
    all_tables = {id(t): i + 1 for i, t in enumerate(content.find_all("table"))}
    result = []
    for node in start.next_elements:
        if isinstance(node, Tag):
            if node.name in HEADINGS and int(node.name[1]) <= rank:
                break
            if node.name == "table" and id(node) in all_tables:
                if node.find_parent("table"):
                    raise ValueError("Nested detail table needs review")
                result.append((all_tables[id(node)], node, anchor))
    return result


def background_gray(tag: Tag) -> bool:
    return bool(re.search(r"background-color\s*:\s*(?:gainsboro|#dcdcdc|rgb\(\s*220\s*,\s*220\s*,\s*220\s*\))",
                          tag.get("style", ""), re.I)) or tag.get("bgcolor", "").lower() in ("gainsboro", "#dcdcdc")


def node_kind(effect: Cell) -> str:
    value = effect.value
    if background_gray(effect.tag):
        return "panel_live"
    if re.search(r"\[コスト\s*:", value):
        return "quick_skill"
    if "(アビリティ)" in value or "（アビリティ）" in value:
        return "unique_ability"
    if "上限+" in value:
        return "cap_increase"
    if "[条件:" in value and "[確率:" in value:
        return "panel_passive"
    raise ValueError("Unclassified panel effect; no candidate adopted")


def parse_panel(tables) -> tuple[list[dict], list[dict]]:
    panels = [(n, t, a) for n, t, a in tables
              if any(text(c) == "SP" for c in t.find_all(["th", "td"]))]
    if len(panels) != 1:
        raise ValueError("Expected exactly one SP panel table")
    number, table, anchor = panels[0]
    grid = table_grid(table)
    nodes = []
    for r, cells in enumerate(grid):
        sp_cell = cells[0]
        if sp_cell.row != r or not sp_cell.value.isdecimal():
            continue
        if r + 1 >= len(grid):
            raise ValueError("Panel name row has no effect row")
        for name in cells[1:]:
            if name.row != r or name.column == 0 or name.tag.name != "th" or not name.value:
                continue
            if cells[name.column] is not name:
                continue
            # Colspans must only create one node.
            if any(n["source_positions"][0]["row"] == r + 1 and
                   n["source_positions"][0]["column"] == name.column + 1 for n in nodes):
                continue
            effect = grid[r + 1][name.column]
            if effect is name or effect.row != r + 1 or effect.column != name.column or effect.colspan != name.colspan:
                raise ValueError("Panel name/effect spans do not match")
            kind = node_kind(effect)
            value = effect.value
            node = {"kind": kind, "name": name.value, "sp": int(sp_cell.value),
                    "unlock_star": int(m[1]) if (m := re.search(r"☆(\d+)", name.value)) else None,
                    "unlock_event": m[1] if (m := re.search(r"\bE(\d+)\b", name.value)) else None,
                    "effect_private": value, "mechanics": mechanics(value) if kind == "panel_live" else [],
                    "source_positions": [evidence(number, name, anchor), evidence(number, effect, anchor)]}
            if kind == "cap_increase":
                match = re.fullmatch(r"(Vocal|Dance|Visual|メンタル)上限\+(\d+)", value)
                if not match:
                    raise ValueError("Unparsed cap increase")
                node.update(cap_target=match[1], cap_delta=int(match[2]))
            if kind == "quick_skill":
                match = re.search(r"\[コスト\s*:\s*(\d+)\]", value)
                if not match:
                    raise ValueError("Unparsed quick-skill cost")
                node["energy_cost"] = int(match[1])
            nodes.append(node)
    if not nodes:
        raise ValueError("Empty panel")
    mb = []
    for number, table, anchor in tables:
        if table is panels[0][1]:
            continue
        if "メモリーブースト" not in text(table) and "[MB]" not in text(table):
            raise ValueError("Unknown extra table in skill-panel section")
        grid = table_grid(table)
        for r, cells in enumerate(grid):
            for c, name in enumerate(cells):
                if name.row != r or name.column != c or "[MB]" not in name.value:
                    continue
                stage = re.search(r"[（(](\d+)/(\d+)[)）]", name.value)
                if not stage or r + 1 >= len(grid):
                    raise ValueError("MB stage/effect missing")
                effect = grid[r + 1][c]
                if effect.row != r + 1 or effect.column != c or not background_gray(effect.tag):
                    raise ValueError("MB name/effect mismatch")
                mb.append({"kind": "mb_live", "name": name.value,
                           "mb_stage": int(stage[1]), "mb_total_stages": int(stage[2]),
                           "effect_private": effect.value, "mechanics": mechanics(effect.value),
                           "base_panel_link": "needs_review",
                           "source_positions": [evidence(number, name, anchor), evidence(number, effect, anchor)]})
        if not mb:
            raise ValueError("MB table without parsed skills")
    return nodes, mb


def parse_memory(tables) -> list[dict]:
    if len(tables) != 1:
        raise ValueError("Expected one memory-appeal table")
    number, table, anchor = tables[0]
    grid = table_grid(table)
    headers = {cell.value: c for c, cell in enumerate(grid[0])}
    if not {"スキル名", "効果"}.issubset(headers):
        raise ValueError("Unknown memory-appeal columns")
    records = []
    for r, cells in enumerate(grid[1:], 1):
        name, effect = cells[headers["スキル名"]], cells[headers["効果"]]
        match = re.search(r"思い出アピール\[Lv(\d+)\]", effect.value)
        if not match:
            raise ValueError("Unparsed memory-appeal row")
        record = {"kind": "memory_appeal", "level": int(match[1]), "name": name.value,
                  "effect_private": effect.value,
                  "source_positions": [evidence(number, name, anchor), evidence(number, effect, anchor)]}
        for label, field in (("リンクアピール", "link_appeal_private"), ("チャージアピール", "charge_appeal_private")):
            record[field] = cells[headers[label]].value if label in headers else None
            if label in headers:
                record["source_positions"].append(evidence(number, cells[headers[label]], anchor))
        records.append(record)
    levels = [x["level"] for x in records]
    if not levels or len(set(levels)) != len(levels) or sorted(levels) != list(range(1, max(levels) + 1)):
        raise ValueError("Missing or duplicate memory levels")
    return records


def match_abilities(nodes, tables):
    abilities = [n for n in nodes if n["kind"] == "unique_ability"]
    if not tables:
        return
    entries = []
    for number, table, anchor in tables:
        for cells in table_grid(table):
            name, effect = cells[0], cells[-1]
            if name.value in ("スキル名", "アビリティ名", "名称"):
                continue
            entries.append((name.value, effect.value, evidence(number, name, anchor), evidence(number, effect, anchor)))
    if len(entries) != len(abilities):
        raise ValueError("Panel/ability section counts differ")
    for ability in abilities:
        expected = re.sub(r"^[（(]アビリティ[)）]\s*", "", ability["effect_private"])
        matching = [e for e in entries if e[:2] == (ability["name"], expected)]
        if len(matching) != 1:
            raise ValueError("Panel/ability section content differs")
        ability["source_positions"].extend(matching[0][2:])
        ability["second_section_confirmed"] = True


def extract_html(raw: bytes, card: dict) -> dict:
    """Only P HTML is enabled until S tables have a saved real HTML fixture."""
    if card["card_kind"] != "P":
        raise ValueError("S HTML parser not verified yet; keep input for offline replay")
    soup = BeautifulSoup(raw, "html.parser")
    links = soup.select('link[rel="canonical"]')
    if len(links) != 1 or wiki_key(links[0].get("href", "")) != wiki_key(card["wiki_url"]):
        raise ValueError("Wiki canonical/card URL mismatch")
    content = soup.select_one("#content")
    if not content or not soup.title or not text(soup.title).startswith(card["card_title"] + card["idol_name"]):
        raise ValueError("Missing Wiki content or wrong card title")
    if tables_in(content, "所持スキル", optional=True):
        raise ValueError("P/S section mismatch")
    nodes, mb = parse_panel(tables_in(content, "スキルパネル"))
    abilities = tables_in(content, "アビリティ", optional=True)
    match_abilities(nodes, abilities)
    memory = parse_memory(tables_in(content, "思い出アピール"))
    return {"card_id": card["card_id"], "card_kind": "P", "card_title": card["card_title"],
            "wiki_url": card["wiki_url"], "source_kind": "saved_wiki_html",
            "source_sha256": hashlib.sha256(raw).hexdigest(), "panel_nodes": nodes,
            "mb_live": mb, "memory_appeals": memory,
            "coverage": {"skill_panel": "extracted", "memory_appeal": "extracted",
                         "memory_boost": "extracted" if mb else "no_entry_confirmed",
                         "unique_ability": "extracted" if any(n["kind"] == "unique_ability" for n in nodes) else "no_entry_confirmed",
                         "stage_skill": "not_collected", "aptitude": "not_collected",
                         "review": "needs_review"}}


def transform_run(directory: Path, card: dict, base_version: str) -> dict:
    report = json.loads((directory / "fetch.json").read_text(encoding="utf-8"))
    raw = (directory / "response.html").read_bytes()
    if report.get("status") != "fetched" or report.get("http_status") != 200:
        raise ValueError("Saved acquisition was not successful")
    if report.get("sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError("Saved HTML hash mismatch")
    if wiki_key(report["url"]) != wiki_key(card["wiki_url"]):
        raise ValueError("Saved acquisition URL/card mismatch")
    try:
        stamp = datetime.fromisoformat(report["fetched_at"].replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError("Missing timestamp timezone")
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ValueError("Invalid acquisition timestamp") from error
    record = extract_html(raw, card)
    record["fetched_at"] = report["fetched_at"]
    result = {"pilot_schema": "0.2", "base_dataset_version": base_version,
              "input_kind": "saved_wiki_html", "cards": [record]}
    stable = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    result["content_hash"] = hashlib.sha256(stable.encode("utf-8")).hexdigest()
    return result
