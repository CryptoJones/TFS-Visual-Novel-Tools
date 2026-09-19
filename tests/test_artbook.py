from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tfs_vn.artbook import load_artbook_config, parse_index


class ArtbookConfigTests(unittest.TestCase):
    def test_parse_markdown_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index = Path(tmp) / "art-review-index.md"
            index.write_text(
                "| Plate | Type | Source | Prompt |\n"
                "| --- | --- | --- | --- |\n"
                "| P001 | room | `assets/backgrounds_hd/foyer.png` | Quiet foyer |\n",
                encoding="utf-8",
            )
            rows = parse_index(index)

        self.assertEqual(rows[0]["plate"], "P001")
        self.assertEqual(rows[0]["source"], "assets/backgrounds_hd/foyer.png")
        self.assertEqual(rows[0]["text"], "Quiet foyer")

    def test_load_artbook_config_resolves_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # The loader returns resolved absolute paths, and on macOS the
            # tempdir is a symlink (/var -> /private/var), so resolve the
            # expectation root too or the comparison can never match.
            root = Path(tmp).resolve()
            config_path = root / "artbook.json"
            config_path.write_text(
                json.dumps(
                    {
                        "title": "The Art",
                        "subtitle": "Demo",
                        "out": "out/book.pdf",
                        "asset_dir": "plates",
                        "plates": [{"plate": "P001", "source": "foyer.png"}],
                    }
                ),
                encoding="utf-8",
            )
            config = load_artbook_config(config_path)

        self.assertEqual(config["title"], "The Art")
        self.assertEqual(config["out"], root / "out/book.pdf")
        self.assertEqual(config["asset_dir"], root / "plates")
        self.assertEqual(config["plates"][0]["source"], "foyer.png")


if __name__ == "__main__":
    unittest.main()
