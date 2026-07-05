"""Command-line entry point for TFS Visual Novel Tools."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import __version__
from .config import ConfigError, write_json
from .scaffold import example_project_config, scaffold_from_config, scaffold_project
from .validate import ValidationError, run_godot_checks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tfs-vn", description="Build reusable Godot visual novels.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scaffold = sub.add_parser("scaffold", help="Create a runnable Godot project from project.json.")
    p_scaffold.add_argument("--config", required=True, help="Project config JSON.")
    p_scaffold.add_argument("--out", help="Output project directory. Overrides config out.")
    p_scaffold.add_argument("--template", help="Engine template directory.")
    p_scaffold.add_argument("--force", action="store_true", help="Replace an existing non-empty output directory.")
    p_scaffold.add_argument("--no-validate", action="store_true", help="Skip Godot validation after scaffolding.")
    p_scaffold.add_argument("--godot", default="godot", help="Godot executable name/path.")
    p_scaffold.set_defaults(func=_cmd_scaffold)

    p_demo = sub.add_parser("demo", help="Create a runnable demo project.")
    p_demo.add_argument("--out", required=True, help="Output project directory.")
    p_demo.add_argument("--template", help="Engine template directory.")
    p_demo.add_argument("--force", action="store_true", help="Replace an existing non-empty output directory.")
    p_demo.add_argument("--no-validate", action="store_true", help="Skip Godot validation after scaffolding.")
    p_demo.add_argument("--godot", default="godot", help="Godot executable name/path.")
    p_demo.set_defaults(func=_cmd_demo)

    p_validate = sub.add_parser("validate", help="Run the Godot data/playthrough checks.")
    p_validate.add_argument("--project", required=True, help="Godot project directory.")
    p_validate.add_argument("--godot", default="godot", help="Godot executable name/path.")
    p_validate.set_defaults(func=_cmd_validate)

    p_artbook = sub.add_parser("artbook", help="Build an art-book PDF from artbook.json.")
    p_artbook.add_argument("--config", required=True, help="Artbook config JSON.")
    p_artbook.add_argument("--no-compress", action="store_true", help="Skip Ghostscript compression.")
    p_artbook.set_defaults(func=_cmd_artbook)

    p_wizard = sub.add_parser("wizard", help="Launch the desktop configurator.")
    p_wizard.set_defaults(func=_cmd_wizard)
    return parser


def _cmd_scaffold(args: argparse.Namespace) -> int:
    out = scaffold_from_config(
        args.config,
        args.out,
        template=args.template,
        force=args.force,
        run_validation=not args.no_validate,
        godot=args.godot,
    )
    print(f"wrote Godot project: {out}")
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    out = scaffold_project(
        example_project_config(),
        args.out,
        config_dir=Path.cwd(),
        template=args.template,
        force=args.force,
        run_validation=not args.no_validate,
        godot=args.godot,
    )
    write_json(Path(out) / "project.tfs-vn.json", example_project_config())
    print(f"wrote demo project: {out}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    results = run_godot_checks(args.project, godot=args.godot)
    ok = True
    for result in results:
        status = "OK" if result.ok else f"FAIL {result.returncode}"
        print(f"{result.name}: {status}")
        if result.stdout:
            print(result.stdout.rstrip())
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        ok = ok and result.ok
    return 0 if ok else 1


def _cmd_artbook(args: argparse.Namespace) -> int:
    from .artbook import build_artbook_from_config

    result = build_artbook_from_config(args.config, compress=not args.no_compress)
    print(f"wrote artbook: {result['out']} ({result['pages']} pages, {result['plates']} plates)")
    return 0


def _cmd_wizard(_args: argparse.Namespace) -> int:
    from .wizard import main as wizard_main

    wizard_main()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (ConfigError, ValidationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
