# CLI Reference

Install in editable mode from the repo root:

```sh
python3 -m pip install -e .
```

The command entry point is `tfs-vn`.

## Create a Demo Project

```sh
tfs-vn demo --out /tmp/my-vn
godot --path /tmp/my-vn
```

## Scaffold a Project

```sh
tfs-vn scaffold --config project.json --out ./build/my-vn
```

Useful flags:

- `--force` replaces an existing non-empty output directory.
- `--no-validate` skips the Godot checks.
- `--template /path/to/engine` uses a different engine template.
- `--godot /path/to/godot` selects a specific Godot binary.

## Validate a Project

```sh
tfs-vn validate --project ./build/my-vn
```

This runs:

```sh
godot --headless --path ./build/my-vn --script res://tests/validate_data.gd
godot --headless --path ./build/my-vn --script res://tests/playthrough.gd
godot --headless --path ./build/my-vn res://tests/playtest.tscn
```

The first two check the data. The **playtest** boots the real game and plays it:

- lays out every room description and dialog passage at every Text Size, and
  scrolls an over-tall passage with real mouse-wheel events;
- checks that every chapter story card with art to borrow carries a plate that
  loads;
- where a chapter's quest requires scenes, proves the chapter cannot be concluded
  by walking through it, and can be once the last scene is heard;
- plays every chapter as an **impatient reader** — legal moves only, always
  pushing ahead, talking only when blocked — and fails on a soft-lock. Checks
  that teleport between rooms cannot see "walked past a required scene into a
  room with no way back"; this one can.

It derives what to expect from the game's own data, so it needs no editing per
game. Each check is killed and reported as failed after 15 minutes rather than
hanging the scaffolder.

## Build an Art Book

```sh
tfs-vn artbook --config artbook.json
```

`tools/artbook/build_artbook.py` is kept as a wrapper:

```sh
python3 tools/artbook/build_artbook.py --config artbook.json
```

## Launch the Wizard

```sh
tfs-vn wizard
```

or:

```sh
python3 tools/configurator/app.py
```
