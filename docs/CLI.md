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
```

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
