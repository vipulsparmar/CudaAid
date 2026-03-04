"""Automated fix / dry-run pipeline.

Generates the shell commands that would resolve detected issues and
optionally executes them.  Visual styling matches the reporter theme.
"""

from __future__ import annotations

import subprocess

from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from ai_doctor.models import EnvironmentReport, Recommendation, Status

# ── Theme tokens (shared with reporter) ──────────────────────────────────────
_ACCENT     = "#5eead4"
_ACCENT_DIM = "#115e59"
_DIM        = "#64748b"
_VALUE      = "#f1f5f9"
_BORDER     = "#334155"
_FG_OK      = "#6ee7b7"
_FG_WARN    = "#fcd34d"
_FG_ERR     = "#fca5a5"
_BG_OK      = "#065f46"
_BG_WARN    = "#78350f"
_BG_ERR     = "#7f1d1d"

console = Console()


def generate_fix_commands(report: EnvironmentReport) -> list[str]:
    """Return a list of shell commands that would fix detected issues."""
    commands: list[str] = []

    for rec in report.recommendations:
        if rec.pip_command:
            commands.append(rec.pip_command)

    # If torch is missing entirely, suggest the recommended build
    if not report.torch.installed and not commands:
        commands.append(
            "pip install torch --index-url https://download.pytorch.org/whl/cu121"
        )

    return commands


def apply_fixes(report: EnvironmentReport, *, dry_run: bool = True) -> None:
    """Display and optionally execute fix commands.

    Parameters
    ----------
    report:
        The environment report from the analysis phase.
    dry_run:
        When True (default), only print the commands without running them.
    """
    commands = generate_fix_commands(report)

    if not commands:
        console.print()
        console.print(
            Panel(
                f"[bold {_FG_OK} on {_BG_OK}]  ✓  ALL CLEAR  [/bold {_FG_OK} on {_BG_OK}]"
                f"\n\n  [{_DIM}]No fixable issues detected — your environment looks good.[/{_DIM}]",
                border_style=_BG_OK,
                padding=(1, 2),
                expand=True,
            )
        )
        console.print()
        return

    # ── Mode banner ──────────────────────────────────────────────────────────
    console.print()
    if dry_run:
        mode_badge = f"[bold {_FG_WARN} on {_BG_WARN}]  ▶  DRY RUN  [/bold {_FG_WARN} on {_BG_WARN}]"
        border_color = _BG_WARN
        subtitle = "The following commands will be shown but [bold]not[/bold] executed."
    else:
        mode_badge = f"[bold {_FG_ERR} on {_BG_ERR}]  ▶  APPLYING FIXES  [/bold {_FG_ERR} on {_BG_ERR}]"
        border_color = _BG_ERR
        subtitle = "The following commands will be executed now."

    console.print(
        Panel(
            f"{mode_badge}\n\n  [{_DIM}]{subtitle}[/{_DIM}]",
            border_style=border_color,
            padding=(1, 2),
            expand=True,
        )
    )
    console.print()

    # ── Command list ─────────────────────────────────────────────────────────
    table = Table(
        show_header=True,
        show_edge=False,
        show_lines=False,
        box=None,
        padding=(0, 2),
        expand=True,
    )
    table.add_column("#", style=f"bold {_DIM}", width=4, justify="right")
    table.add_column("Command", style=f"bold {_FG_OK}")

    for idx, cmd in enumerate(commands, 1):
        table.add_row(str(idx), f"$ {cmd}")

    console.print(
        Panel(
            table,
            border_style=_BORDER,
            padding=(1, 2),
            expand=True,
        )
    )
    console.print()

    if dry_run:
        console.print(
            f"  [{_DIM}]Remove [bold]--dry-run[/bold] to execute:  "
            f"[bold]ai-doctor fix[/bold][/{_DIM}]"
        )
        console.print()
        return

    # ── Execute ──────────────────────────────────────────────────────────────
    for idx, cmd in enumerate(commands, 1):
        console.print(Rule(style=_BORDER))
        console.print(
            f"  [{_DIM}]Step {idx}/{len(commands)}[/{_DIM}]  "
            f"[bold {_VALUE}]{cmd}[/bold {_VALUE}]"
        )
        console.print()

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                text=True,
                capture_output=True,
                timeout=300,
            )
            if result.returncode == 0:
                console.print(
                    f"  [{_FG_OK} on {_BG_OK}] ✓ DONE [/{_FG_OK} on {_BG_OK}]"
                )
                if result.stdout.strip():
                    for line in result.stdout.strip().splitlines()[-5:]:
                        console.print(f"    [{_DIM}]{line}[/{_DIM}]")
            else:
                console.print(
                    f"  [{_FG_ERR} on {_BG_ERR}] ✗ FAILED (exit {result.returncode}) [/{_FG_ERR} on {_BG_ERR}]"
                )
                if result.stderr.strip():
                    for line in result.stderr.strip().splitlines()[-5:]:
                        console.print(f"    [{_FG_ERR}]{line}[/{_FG_ERR}]")
        except subprocess.TimeoutExpired:
            console.print(
                f"  [{_FG_ERR} on {_BG_ERR}] ✗ TIMEOUT [/{_FG_ERR} on {_BG_ERR}]"
            )
        except Exception as exc:
            console.print(
                f"  [{_FG_ERR} on {_BG_ERR}] ✗ ERROR [/{_FG_ERR} on {_BG_ERR}]  "
                f"[{_FG_ERR}]{exc}[/{_FG_ERR}]"
            )
        console.print()

    console.print(Rule(style=_BORDER))
    console.print(
        f"  [{_DIM}]Run [bold]ai-doctor check[/bold] to verify the changes.[/{_DIM}]"
    )
    console.print()
