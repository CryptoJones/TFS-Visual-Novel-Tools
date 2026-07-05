"""Run the Godot validation scripts shipped with generated projects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess


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
    scripts = [
        ("validate_data", "res://tests/validate_data.gd"),
        ("playthrough", "res://tests/playthrough.gd"),
    ]
    results: list[CheckResult] = []
    for name, script in scripts:
        cmd = [str(executable), "--headless", "--path", str(project_dir), "--script", script]
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
        results.append(CheckResult(name, cmd, proc.returncode, proc.stdout, proc.stderr))
    return results


def validate_project(project: str | Path, godot: str = "godot") -> list[CheckResult]:
    results = run_godot_checks(project, godot=godot)
    failed = [r for r in results if not r.ok]
    if failed:
        detail = "\n".join(f"{r.name}: exit {r.returncode}\n{r.stdout}{r.stderr}" for r in failed)
        raise ValidationError(detail)
    return results
