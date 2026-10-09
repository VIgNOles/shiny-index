"""Offline extraction of saved Wiki HTML into private detail candidates."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from unicodedata import normalize

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


def parse_panel(tables, *, notes=None) -> tuple[list[dict], list[dict]]:
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
                attribute = r"(?:Vocal|Dance|Visual|メンタル)"
                match = re.fullmatch(rf"({attribute}(?:\s*&\s*{attribute})*)\s*上限\+(\d+)", value)
                if not match:
                    raise ValueError("Unparsed cap increase")
                targets = [x.strip() for x in match[1].split("&")]
                if len(set(targets)) != len(targets):
                    raise ValueError("Duplicate cap target")
                node.update(cap_targets=targets, cap_delta=int(match[2]))
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
            explanation=table_grid(table)
            if (notes is not None and len(explanation)==2 and all(len(row)==1 for row in explanation)
                    and explanation[0][0].tag.name=='th' and explanation[1][0].tag.name=='td'
                    and explanation[0][0].value and explanation[1][0].value):
                notes.append({'name':explanation[0][0].value,'effect_private':explanation[1][0].value,
                              'source_positions':[evidence(number,row[0],anchor) for row in explanation]})
                continue
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
    main=[];conditions=[]
    for number,table,anchor in tables:
        grid=table_grid(table)
        if {"スキル名","効果"}.issubset({cell.value for cell in grid[0]}):
            main.append((number,table,anchor));continue
        if len(grid)!=1 or len(grid[0])<2 or grid[0][0].value!="思い出アピールリンク条件":
            raise ValueError("Unknown extra memory-appeal table")
        cells=grid[0][1:]
        if any(not cell.value and not cell.tag.find('img') for cell in cells):
            raise ValueError("Empty memory-link condition")
        conditions.append({'text_private':[cell.value for cell in cells],
                           'image_refs_private':[{'alt':img.get('alt'),'title':img.get('title'),'src':img.get('src')}
                                                 for cell in cells for img in cell.tag.find_all('img')],
                           'source_positions':[evidence(number,cell,anchor) for cell in grid[0]]})
    if len(main) != 1:
        raise ValueError("Expected one memory-appeal table")
    if len(conditions)>1:raise ValueError("Duplicate memory-link condition table")
    number, table, anchor = main[0]
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
        if conditions:
            record['link_condition_private']=conditions[0]
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
    if not abilities and entries:
        if len({(entry[0],entry[1]) for entry in entries})!=len(entries):raise ValueError("Duplicate dedicated ability")
        for name,effect,*positions in entries:
            nodes.append({'kind':'unique_ability','name':name,'sp':None,'effect_private':effect,
                          'mechanics':[],'source_positions':positions,'origin':'ability_section',
                          'second_section_confirmed':False})
        return
    if len(entries) != len(abilities):
        raise ValueError("Panel/ability section counts differ")
    for ability in abilities:
        expected = re.sub(r"^[（(]アビリティ[)）]\s*", "", ability["effect_private"])
        matching = [e for e in entries if e[:2] == (ability["name"], expected)]
        if len(matching) != 1:
            raise ValueError("Panel/ability section content differs")
        ability["source_positions"].extend(matching[0][2:])
        ability["second_section_confirmed"] = True


def parse_s_traits(content: Tag) -> dict:
    table = content.find("table")
    if table is None:
        raise ValueError("Missing S basic-information table")
    values, sources = {}, {}
    for cells in table_grid(table):
        label = cells[0].value
        if label not in ("アイデア", "ひらめき", "楽曲熟練度"):
            continue
        if label in values:
            raise ValueError("Duplicate S trait")
        entries = [cell for c, cell in enumerate(cells[1:], 1) if cell.column == c]
        if not entries or any(not cell.value for cell in entries):
            raise ValueError("Missing S trait value")
        values[label] = [cell.value for cell in entries]
        sources[label] = [evidence(1, cell, None) for cell in entries]
    if set(values) != {"アイデア", "ひらめき", "楽曲熟練度"} or any(
            len(values[label]) != 1 for label in ("アイデア", "ひらめき")):
        raise ValueError("Missing or ambiguous S traits")
    return {"idea": values["アイデア"][0], "inspiration": values["ひらめき"][0],
            "music_proficiencies": values["楽曲熟練度"], "source_positions": sources}


def parse_s_status(tables) -> dict:
    if len(tables) != 1:
        raise ValueError("Expected one S status table")
    number, table, anchor = tables[0]
    grid = table_grid(table)
    labels = [cell.value for cell in grid[0]]
    expected = {"Lv", "Vo", "Da", "Vi", "メンタル"}
    if set(labels) != expected or len(labels) != len(expected):
        raise ValueError("Unknown S status columns")
    columns = {label: labels.index(label) for label in labels}
    rows = []
    for cells in grid[1:]:
        lv = cells[columns["Lv"]]
        match = re.fullmatch(r"(\d+)(?:[（(]☆(\d+)[）)])?", lv.value.replace(" ", ""))
        if not match:
            raise ValueError("Unknown S status level")
        rows.append((int(match[1]), int(match[2]) if match[2] else None, cells))
    if not rows or len({row[0] for row in rows}) != len(rows):
        raise ValueError("Missing or duplicate S status levels")
    level, star, cells = max(rows, key=lambda row: row[0])
    record = {"level": level, "limit_break": star, "source_positions": [evidence(number, cells[columns["Lv"]], anchor)]}
    missing = []
    for label, field in (("Vo", "vocal"), ("Da", "dance"), ("Vi", "visual"), ("メンタル", "mental")):
        cell = cells[columns[label]]
        if cell.value.isdecimal():
            record[field] = int(cell.value)
        elif cell.value in ("", "?", "？", "-", "―", "不明", "未記載"):
            record[field] = None
            missing.append(field)
        else:
            raise ValueError("Unrecognized S status value")
        record["source_positions"].append(dict(evidence(number, cell, anchor), field=field))
    if missing:
        record["missing_fields"] = missing
    return record


def parse_possessed_live(tables) -> list[dict]:
    if len(tables) != 1:
        raise ValueError("Expected one possessed-live table")
    number, table, anchor = tables[0]
    grid = table_grid(table)
    labels = [cell.value for cell in grid[0]]
    if set(labels) != {"スキル名", "効果", "取得Lv"} or len(labels) != 3:
        raise ValueError("Unknown possessed-live columns")
    columns = {label: labels.index(label) for label in labels}
    records = []
    for cells in grid[1:]:
        name, effect, level = [cells[columns[label]] for label in ("スキル名", "効果", "取得Lv")]
        if not name.value or not effect.value or not (level.value == "初期" or level.value.isdecimal()):
            raise ValueError("Invalid possessed-live row")
        records.append({"kind": "possessed_live", "name": name.value, "effect_private": effect.value,
                        "acquired_at_level": level.value, "mechanics": mechanics(effect.value),
                        "source_positions": [evidence(number, cell, anchor) for cell in (name, effect, level)]})
    if not records or len({(x["name"], x["acquired_at_level"]) for x in records}) != len(records):
        raise ValueError("Empty or duplicate possessed-live skills")
    return records


def parse_support_skills(tables) -> list[dict]:
    if len(tables) != 1:
        raise ValueError("Expected one support-skill table")
    number, table, anchor = tables[0]
    grid = table_grid(table)
    if len(grid) < 3 or grid[0][0].value != "スキル名" or grid[0][1].value != "スキル効果":
        raise ValueError("Unknown support-skill headers")
    labels = [cell.value for cell in grid[1][2:]]
    numeric = [int(value) for value in labels if value.isdecimal()]
    if (not numeric or len(set(labels)) != len(labels) or numeric != sorted(numeric) or
            any(not value.isdecimal() and value != "最大" for value in labels) or
            ("最大" in labels and labels[-1] != "最大")):
        raise ValueError("Unknown support-skill level columns")
    records = []
    for cells in grid[2:]:
        name, effect = cells[:2]
        if not name.value or not effect.value:
            raise ValueError("Missing support-skill name or effect")
        progression = []
        for c, label in enumerate(labels, 2):
            cell = cells[c]
            if not cell.value:
                continue
            if not cell.value.isdecimal():
                raise ValueError("Unparsed support-skill progression")
            progression.append({"support_level": label, "skill_level": int(cell.value),
                                "source_positions": [evidence(number, grid[1][c], anchor),
                                                     evidence(number, cell, anchor)]})
        if not progression:
            raise ValueError("Support skill has no progression")
        records.append({"kind": "support_skill", "name": name.value, "effect_private": effect.value,
                        "progression": progression,
                        "source_positions": [evidence(number, name, anchor), evidence(number, effect, anchor)]})
    if not records or len({record["name"] for record in records}) != len(records):
        raise ValueError("Empty or duplicate support skills")
    return records


def extract_html(raw: bytes, card: dict, *, variant_cards=None) -> dict:
    """Extract P/S facts without article commentary or excluded skill sections."""
    if card["card_kind"] not in ("P", "S"):
        raise ValueError("Unknown card kind")
    soup = BeautifulSoup(raw, "html.parser")
    links = soup.select('link[rel="canonical"]')
    if len(links) != 1 or wiki_key(links[0].get("href", "")) != wiki_key(card["wiki_url"]):
        raise ValueError("Wiki canonical/card URL mismatch")
    content = soup.select_one("#content")
    title_card=card
    if variant_cards is not None:
        from src.detail_variants import validate_variants,select_variant_tables
        title_card=validate_variants(variant_cards)
        if not any(c==card for c in variant_cards):raise ValueError('Shared card identity mismatch')
    if not content or not soup.title or not normalize('NFKC',text(soup.title)).startswith(normalize('NFKC',title_card["card_title"] + title_card["idol_name"])):
        raise ValueError("Missing Wiki content or wrong card title")
    def section(heading,optional=False):
        tables=tables_in(content,heading,optional=optional)
        return select_variant_tables(tables,variant_cards,card['card_id'],required=not optional) if variant_cards is not None else tables
    notes=[]
    nodes, mb = parse_panel(section("スキルパネル"),notes=notes)
    record = {"card_id": card["card_id"], "card_kind": card["card_kind"], "card_title": card["card_title"],
              "wiki_url": card["wiki_url"], "source_kind": "saved_wiki_html",
              "source_sha256": hashlib.sha256(raw).hexdigest(), "panel_nodes": nodes,
              "coverage": {"skill_panel": "extracted", "review": "needs_review"}}
    if notes:record["skill_notes_private"]=notes
    if variant_cards is not None:record["variant_mapping"]={"variant_kind":card["variant_kind"],"rarity":card["rarity"],"basis":"explicit_fold_labels"}
    if card["card_kind"] == "P":
        if tables_in(content, "所持スキル", optional=True):
            raise ValueError("P/S section mismatch")
        match_abilities(nodes, section("アビリティ",optional=True))
        record["mb_live"] = mb
        record["memory_appeals"] = parse_memory(section("思い出アピール"))
        record["coverage"].update({
            "memory_appeal": "extracted", "memory_boost": "extracted" if mb else "no_entry_confirmed",
            "unique_ability": "extracted" if any(n["kind"] == "unique_ability" for n in nodes) else "no_entry_confirmed",
            "stage_skill": "not_collected", "aptitude": "not_collected"})
    else:
        if tables_in(content, "思い出アピール", optional=True) or mb:
            raise ValueError("P/S section mismatch")
        record["traits"] = parse_s_traits(content)
        record["max_status"] = parse_s_status(tables_in(content, "ステータス"))
        record["possessed_live"] = parse_possessed_live(tables_in(content, "ライブスキル"))
        record["support_skills"] = parse_support_skills(tables_in(content, "サポートスキル"))
        record["coverage"].update({"traits": "extracted", "max_status": "partial_missing_values" if record["max_status"].get("missing_fields") else "extracted",
                                   "possessed_live": "extracted", "support_skills": "extracted",
                                   "quick_skill": "extracted" if any(n["kind"] == "quick_skill" for n in nodes) else "no_entry_confirmed",
                                   "fight_skill": "not_collected"})
    return record


def transform_run(directory: Path, card: dict, base_version: str, *, variant_cards=None) -> dict:
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
    record = extract_html(raw, card,variant_cards=variant_cards)
    record["fetched_at"] = report["fetched_at"]
    result = {"pilot_schema": "0.3", "base_dataset_version": base_version,
              "input_kind": "saved_wiki_html", "cards": [record]}
    stable = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    result["content_hash"] = hashlib.sha256(stable.encode("utf-8")).hexdigest()
    return result
