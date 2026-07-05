#!/usr/bin/env python3
"""Compatibility wrapper for the config-driven artbook CLI.

Use:
  tfs-vn artbook --config artbook.json
  python3 tools/artbook/build_artbook.py --config artbook.json
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tfs_vn.artbook import build_artbook_from_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a TFS visual novel art-book PDF.")
    parser.add_argument("--config", required=True, help="Artbook config JSON.")
    parser.add_argument("--no-compress", action="store_true", help="Skip Ghostscript compression.")
    args = parser.parse_args(argv)
    result = build_artbook_from_config(args.config, compress=not args.no_compress)
    print(f"wrote artbook: {result['out']} ({result['pages']} pages, {result['plates']} plates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
