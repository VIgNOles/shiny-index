"""Meaningful boundaries for the four-card offline detail pilot."""
import unittest
from scripts.transform_detail_sample import (
    clean, mechanics, panel_nodes, s_max_status, support_skills
)


class DetailPilotTests(unittest.TestCase):
    def test_link_labels_can_contain_bracketed_conditions(self):
        self.assertEqual(clean('[[[条件甲]>解説#anchor]]'),'[条件甲]')
        self.assertEqual(clean('[[名称甲>解説]]/[[名称乙>解説]]'),'名称甲/名称乙')
        self.assertEqual(clean('[[単純リンク]] と [[名称甲>解説]]'),'[[単純リンク]] と 名称甲')

    def test_mechanic_aliases_and_scope(self):
        self.assertEqual(
            mechanics("(Link)/(Plus)/(change)/(GrowUp)/(Grow)/(Reflain)/(Refrain)"),
            ["change", "grow", "link", "plus", "refrain"],
        )
        self.assertEqual(mechanics("Dance5倍アピール"), [])

    def test_panel_quick_is_not_passive_or_live(self):
        rows = [
            (10, "|~30|>|~名称|>|~Vocal100%UP|"),
            (11, "|~|>|[コスト:3]|>|[条件:2ターン以前][確率:30%][最大:1回]|"),
        ]
        nodes = panel_nodes(rows)
        self.assertEqual([x["kind"] for x in nodes], ["quick_skill", "panel_passive"])
        self.assertEqual(nodes[0]["energy_cost"], 3)

    def test_max_status_uses_highest_level_and_star(self):
        rows = [
            (1, "|~1|100|50|50|46|"),
            (2, "|~80（☆4）|325|163|163|150|"),
            (3, "|~70（☆2）|287|144|144|132|"),
        ]
        self.assertEqual(
            s_max_status(rows),
            {"level": 80, "limit_break": 4, "vocal": 325, "dance": 163,
             "visual": 163, "mental": 150, "source_lines": [2]},
        )

    def test_support_max_column_is_not_a_numeric_acquisition_level(self):
        rows = [
            (1, "|~|~|~1|~80|~最大|"),
            (2, "|~絆|効果|1|5|5|"),
        ]
        skills = support_skills(rows)
        self.assertEqual(
            skills[0]["progression"],
            [
                {"support_level": "1", "skill_level": 1},
                {"support_level": "80", "skill_level": 5},
                {"support_level": "最大", "skill_level": 5},
            ],
        )


if __name__ == "__main__":
    unittest.main()
