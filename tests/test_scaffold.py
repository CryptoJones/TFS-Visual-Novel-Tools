from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tfs_vn.scaffold import scaffold_project


class ScaffoldTests(unittest.TestCase):
    def test_minimal_project_generates_valid_engine_data(self) -> None:
        config = {
            "title": "Smoke Test",
            "subtitle": "Demo",
            "dedication": "For testers.",
            "accent": "#ff8844",
            "chapters": [
                {
                    "id": "chapter_one",
                    "title": "Chapter One",
                    "rooms": [
                        {"id": "foyer", "name": "Foyer", "desc": "The first room."},
                        {"id": "study", "name": "Study", "desc": "The second room."},
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "game"
            scaffold_project(config, out, config_dir=Path(tmp), run_validation=False)
            chapters = json.loads((out / "data/chapters.json").read_text(encoding="utf-8"))
            rooms = json.loads((out / "data/rooms/chapter_one.json").read_text(encoding="utf-8"))
            quests = json.loads((out / "data/quests.json").read_text(encoding="utf-8"))
            theme = (out / "src/ui/UITheme.gd").read_text(encoding="utf-8")

        self.assertEqual(chapters["game"], "Smoke Test \u2014 Demo")
        self.assertEqual(chapters["dedication"], "For testers.")
        self.assertEqual(rooms["start"], "foyer")
        self.assertEqual(rooms["rooms"]["foyer"]["exits"], {"east": "study"})
        self.assertEqual(rooms["rooms"]["study"]["exits"], {"west": "foyer"})
        self.assertEqual(rooms["rooms"]["study"]["on_enter_flag"], "visited_study")
        self.assertEqual(quests["quests"]["q_chapter_one"]["steps"][0]["flag"], "visited_study")
        self.assertIn('const ACCENT := Color("ff8844")', theme)

    def test_pickups_synthesize_items(self) -> None:
        config = {
            "title": "Pickup Test",
            "chapters": [
                {
                    "id": "chapter",
                    "rooms": [
                        {
                            "id": "room",
                            "name": "Room",
                            "desc": "A room.",
                            "pickups": [{"item": "silver_key", "label": "Take key"}],
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "game"
            scaffold_project(config, out, config_dir=Path(tmp), run_validation=False)
            items = json.loads((out / "data/items.json").read_text(encoding="utf-8"))
            rooms = json.loads((out / "data/rooms/chapter.json").read_text(encoding="utf-8"))

        self.assertIn("silver_key", items["items"])
        self.assertEqual(rooms["rooms"]["room"]["pickups"][0]["label"], "Take key")


if __name__ == "__main__":
    unittest.main()
