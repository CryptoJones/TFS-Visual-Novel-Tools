from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tfs_vn.scaffold import STUDIO_IDENT, scaffold_project


class ScaffoldTests(unittest.TestCase):
    def test_story_cards_borrow_plates_from_their_own_chapter(self) -> None:
        def chapter(cid: str, plates: list[str], **extra) -> dict:
            rooms = [{"id": f"{cid}_{p}", "name": p.title(), "desc": p, "bg": p} for p in plates]
            return {"id": cid, "title": cid, "intro": ["a", "b", "c"], "outro": ["x", "y", "z"], "rooms": rooms, **extra}

        config = {
            "title": "Art Test",
            "chapters": [
                chapter("wide", ["pier", "club", "hall", "attic", "vault", "roof"]),
                chapter("narrow", ["cell"]),
                chapter("pinned", ["pier", "club"], intro_art=["roof", "vault", "attic"], outro_art="hall"),
                {"id": "bare", "title": "bare", "intro": ["a"], "rooms": [{"id": "void", "name": "Void", "desc": "."}]},
            ],
        }

        def build() -> dict:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "game"
                scaffold_project(config, out, config_dir=Path(tmp), run_validation=False)
                doc = json.loads((out / "data/chapters.json").read_text(encoding="utf-8"))
            return {c["id"]: c for c in doc["chapters"]}

        def stems(paths: list[str]) -> list[str]:
            return [Path(p).stem for p in paths]

        chapters = build()
        wide = chapters["wide"]
        self.assertEqual(len(wide["intro_art"]), 3)
        self.assertEqual(len(wide["outro_art"]), 3)
        self.assertTrue(all(p.startswith("res://assets/backgrounds_hd/") and p.endswith(".png") for p in wide["intro_art"]))
        self.assertLessEqual(set(stems(wide["intro_art"] + wide["outro_art"])), {"pier", "club", "hall", "attic", "vault", "roof"})
        # six plates, six cards: the outro never reuses an intro plate
        self.assertEqual(len(set(stems(wide["intro_art"] + wide["outro_art"]))), 6)
        # one plate, three cards: it holds for every card
        self.assertEqual(stems(chapters["narrow"]["intro_art"]), ["cell"] * 3)
        self.assertEqual(stems(chapters["narrow"]["outro_art"]), ["cell"] * 3)
        # explicit art wins, and a single id holds for every card
        self.assertEqual(stems(chapters["pinned"]["intro_art"]), ["roof", "vault", "attic"])
        self.assertEqual(stems(chapters["pinned"]["outro_art"]), ["hall"] * 3)
        # a chapter with no plates stays art-less rather than pointing at nothing
        self.assertEqual(chapters["bare"]["intro_art"], [])
        # seeded: a rebuild never reshuffles the art
        self.assertEqual(build()["wide"]["intro_art"], wide["intro_art"])

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


    def test_studio_ident_is_seeded_after_asset_wipe(self) -> None:
        """The ident is studio branding, so it is re-seeded after the wipe that
        clears the per-game asset folders — a new scaffold shows it with no
        manual copying, while the other asset folders still start clean."""
        config = {
            "title": "Ident Test",
            "chapters": [
                {
                    "id": "chapter",
                    "rooms": [{"id": "room", "name": "Room", "desc": "A room."}],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "game"
            scaffold_project(config, out, config_dir=Path(tmp), run_validation=False)
            ident = out / STUDIO_IDENT
            ui_names = sorted(p.name for p in (out / "assets/ui").iterdir())
            bg_names = sorted(p.name for p in (out / "assets/backgrounds_hd").iterdir())
            # asserted inside the context: the temp tree is gone once it exits
            self.assertTrue(ident.is_file(), f"studio ident not seeded at {STUDIO_IDENT}")
            self.assertEqual(ui_names, [".gitkeep", STUDIO_IDENT.name])
            self.assertEqual(bg_names, [".gitkeep"])


if __name__ == "__main__":
    unittest.main()
