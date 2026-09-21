"""Run the Godot validation scripts shipped with generated projects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess


## A headless Godot run very occasionally never exits; a hung check must fail
## the validation rather than hang the scaffolder forever.
CHECK_TIMEOUT = 900


class ValidationError(RuntimeError):
    """Raised when one or more Godot validation checks fail."""


@dataclass(frozen=True)
class CheckResult:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_godot_checks(project: str | Path, godot: str = "godot") -> list[CheckResult]:
    project_dir = Path(project).expanduser().resolve()
    executable = shutil.which(godot) if not Path(godot).is_absolute() else godot
    if executable is None:
        raise ValidationError(f"Godot executable not found: {godot}")
    base = [str(executable), "--headless", "--path", str(project_dir)]
    checks = [
        ("validate_data", base + ["--script", "res://tests/validate_data.gd"]),
        ("playthrough", base + ["--script", "res://tests/playthrough.gd"]),
    ]
    # The playtest boots the real game, so it runs as a scene, not a --script.
    # It lays out every passage at every Text Size, scrolls an over-tall passage
    # with real mouse-wheel events, checks story-card plates, and plays each
    # chapter as an impatient reader using only legal moves (soft-lock guard).
    if (project_dir / "tests" / "playtest.tscn").exists():
        checks.append(("playtest", base + ["res://tests/playtest.tscn"]))
    results: list[CheckResult] = []
    for name, cmd in checks:
        try:
            proc = subprocess.run(cmd, text=True, capture_output=True, check=False, timeout=CHECK_TIMEOUT)
            results.append(CheckResult(name, cmd, proc.returncode, proc.stdout, proc.stderr))
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode(errors="replace")
            results.append(CheckResult(name, cmd, 124, out, f"timed out after {CHECK_TIMEOUT}s"))
    return results


def validate_project(project: str | Path, godot: str = "godot") -> list[CheckResult]:
    results = run_godot_checks(project, godot=godot)
    failed = [r for r in results if not r.ok]
    if failed:
        detail = "\n".join(f"{r.name}: exit {r.returncode}\n{r.stdout}{r.stderr}" for r in failed)
        raise ValidationError(detail)
    return results
