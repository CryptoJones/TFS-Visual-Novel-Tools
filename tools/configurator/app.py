#!/usr/bin/env python3
"""Launch the TFS visual novel configurator."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tfs_vn.wizard import main


if __name__ == "__main__":
    main()
