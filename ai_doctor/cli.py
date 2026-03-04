"""CLI entry point — thin layer over business logic modules.

All commands follow the same pattern:
1.  Gather data  (gpu / cuda / torch detection)
2.  Analyse      (compatibility engine)
3.  Present      (reporter / fixer)
"""

from __future__ import annotations

import time
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from ai_doctor import __version__
from ai_doctor.compatibility import analyse
from ai_doctor.cuda import detect_cuda
from ai_doctor.fixer import apply_fixes
from ai_doctor.gpu import detect_gpu
from ai_doctor.models import EnvironmentReport
from ai_doctor.reporter import console as report_console
from ai_doctor.reporter import export_json, print_explanation, print_report
from ai_doctor.torch_check import detect_torch

# ── Theme tokens (shared with reporter) ──────────────────────────────────────
_ACCENT = "#5eead4"
_DIM    = "#64748b"
_BORDER = "#334155"
_VALUE  = "#f1f5f9"

app = typer.Typer(
    name="cudaaid",
    help="🩺 CudaAid — detect GPU, CUDA & PyTorch issues.",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

console = Console()


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

_SCAN_STEPS: list[tuple[str, str]] = [
    ("gpu",     "Detecting GPU"),
    ("cuda",    "Detecting CUDA toolkit"),
    ("torch",   "Detecting PyTorch"),
    ("analyse", "Analysing compatibility"),
]


def _gather_report() -> EnvironmentReport:
    """Run all detectors and the compatibility analysis with a styled progress bar."""
    console.print()
    console.print(
        f"  [{_ACCENT}]●[/{_ACCENT}]  "
        f"[bold {_VALUE}]CudaAid[/bold {_VALUE}]  "
        f"[{_DIM}]scanning environment …[/{_DIM}]"
    )
    console.print()

    with Progress(
        SpinnerColumn("dots", style=_ACCENT),
        TextColumn("[bold]{task.description}[/bold]", style=_VALUE),
        BarColumn(bar_width=30, style=_BORDER, complete_style=_ACCENT, finished_style=_ACCENT),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task(_SCAN_STEPS[0][1], total=len(_SCAN_STEPS))

        # Step 1 — GPU
        gpu_info = detect_gpu()
        progress.update(task, advance=1, description=_SCAN_STEPS[1][1])

        # Step 2 — CUDA
        cuda_info = detect_cuda()
        progress.update(task, advance=1, description=_SCAN_STEPS[2][1])

        # Step 3 — PyTorch
        torch_info = detect_torch()
        progress.update(task, advance=1, description=_SCAN_STEPS[3][1])

        # Step 4 — Analyse
        report = analyse(gpu_info, cuda_info, torch_info)
        progress.update(task, advance=1, description="Complete")

    return report


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

@app.command()
def check() -> None:
    """Run a full environment diagnostic and display the report."""
    report = _gather_report()
    print_report(report)


class ExportFormat(str, Enum):
    json = "json"


@app.command()
def export(
    format: ExportFormat = typer.Option(
        ExportFormat.json,
        "--format",
        "-f",
        help="Output format.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file instead of stdout.",
    ),
) -> None:
    """Export the diagnostic report in a machine-readable format."""
    report = _gather_report()

    if format == ExportFormat.json:
        payload = export_json(report)

    if output:
        output.write_text(payload, encoding="utf-8")
        console.print(
            f"  [{_ACCENT}]✓[/{_ACCENT}]  "
            f"[bold {_VALUE}]Report saved →[/bold {_VALUE}]  "
            f"[underline]{output}[/underline]"
        )
        console.print()
    else:
        console.print(payload)


@app.command()
def fix(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show commands without executing them.",
    ),
) -> None:
    """Suggest (or apply) fixes for detected issues."""
    report = _gather_report()
    apply_fixes(report, dry_run=dry_run)


@app.command()
def explain() -> None:
    """Print a human-friendly explanation of the current environment."""
    report = _gather_report()
    print_explanation(report)


@app.callback(invoke_without_command=True)
def version_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        is_eager=True,
    ),
) -> None:
    """Show version information."""
    if version:
        console.print()
        console.print(
            f"  [{_ACCENT}]●[/{_ACCENT}]  "
            f"[bold {_VALUE}]cudaaid[/bold {_VALUE}]  "
            f"[{_DIM}]v{__version__}[/{_DIM}]"
        )
        console.print()
        raise typer.Exit()
