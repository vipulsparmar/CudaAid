"""Rich-powered report rendering — premium DevOps-style output.

All visual output is confined to this module so the rest of the
codebase stays UI-agnostic.

Design language:
  • Docker / kubectl-inspired minimal chrome
  • Monochrome structure + selective colour accents
  • Generous whitespace, no visual clutter
  • Status badges with background highlights
  • Consistent column alignment across sections
"""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from typing import Any

from rich.columns import Columns
from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from ai_doctor import __version__
from ai_doctor.models import EnvironmentReport, Recommendation, Status

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# Theme constants
# ═══════════════════════════════════════════════════════════════════════════════

_ACCENT          = "#5eead4"   # teal-300    — primary accent
_ACCENT_DIM      = "#115e59"   # teal-800    — borders, subtle lines
_BG_OK           = "#065f46"   # emerald-800
_BG_WARN         = "#78350f"   # amber-800
_BG_ERR          = "#7f1d1d"   # red-900
_BG_NA           = "#374151"   # gray-700
_FG_OK           = "#6ee7b7"   # emerald-300
_FG_WARN         = "#fcd34d"   # amber-300
_FG_ERR          = "#fca5a5"   # red-300
_FG_NA           = "#9ca3af"   # gray-400
_LABEL           = "#94a3b8"   # slate-400   — property labels
_VALUE           = "#f1f5f9"   # slate-100   — values
_DIM             = "#64748b"   # slate-500   — secondary text
_BORDER          = "#334155"   # slate-700   — panel borders
_HEADER_GRADIENT = "#0ea5e9"   # sky-500     — header highlight

# Status → colour mapping
_BADGE: dict[Status, tuple[str, str, str]] = {
    #               (icon, fg,      bg)
    Status.OK:        ("✓",  _FG_OK,   _BG_OK),
    Status.WARNING:   ("!",  _FG_WARN, _BG_WARN),
    Status.ERROR:     ("✗",  _FG_ERR,  _BG_ERR),
    Status.NOT_FOUND: ("—",  _FG_NA,   _BG_NA),
}

_STATUS_LABEL: dict[Status, str] = {
    Status.OK:        "PASS",
    Status.WARNING:   "WARN",
    Status.ERROR:     "FAIL",
    Status.NOT_FOUND: "N/A",
}


def _badge(status: Status) -> str:
    """Render a coloured status badge like  ✓ PASS  or  ✗ FAIL ."""
    icon, fg, bg = _BADGE[status]
    label = _STATUS_LABEL[status]
    return f"[{fg} on {bg}] {icon} {label} [/{fg} on {bg}]"


def _icon(status: Status) -> str:
    """Minimal inline icon."""
    icon, fg, _ = _BADGE[status]
    return f"[{fg}]{icon}[/{fg}]"


def _kv(key: str, value: str, *, status: Status | None = None) -> tuple[str, str, str]:
    """Build a (label, value, badge) row tuple."""
    badge = _badge(status) if status else ""
    return (
        f"[{_LABEL}]{key}[/{_LABEL}]",
        f"[bold {_VALUE}]{value}[/bold {_VALUE}]",
        badge,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Public rendering functions
# ═══════════════════════════════════════════════════════════════════════════════

def print_report(report: EnvironmentReport) -> None:
    """Render the full diagnostics report to the terminal."""
    console.print()
    _print_header()
    _print_quick_status(report)
    _print_sections(report)
    _print_compatibility_verdict(report)
    _print_recommendations(report)
    _print_footer()


def print_explanation(report: EnvironmentReport) -> None:
    """Render a human-friendly explanation of the current setup."""
    console.print()
    _print_brand_line()
    console.print()
    console.print(
        Panel(
            _build_explanation_text(report),
            title=f"[bold {_ACCENT}]  Detailed Explanation  [/bold {_ACCENT}]",
            title_align="left",
            border_style=_BORDER,
            padding=(1, 3),
            expand=True,
        )
    )
    _print_footer()


def export_json(report: EnvironmentReport) -> str:
    """Serialize the report to a JSON string."""
    data = _report_to_dict(report)
    return json.dumps(data, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# Header / Footer
# ═══════════════════════════════════════════════════════════════════════════════

_LOGO = r"""
     _    ___     ____             _
    / \  |_ _|   |  _ \  ___   ___| |_ ___  _ __
   / _ \  | |    | | | |/ _ \ / __| __/ _ \| '__|
  / ___ \ | |    | |_| | (_) | (__| || (_) | |
 /_/   \_\___|   |____/ \___/ \___|\__\___/|_|
"""


def _print_header() -> None:
    logo_text = Text(_LOGO.rstrip(), style=f"bold {_ACCENT}")
    subtitle = Text(
        "  GPU · CUDA · PyTorch  Environment Diagnostics",
        style=f"{_DIM}",
    )
    version_text = Text(f"  v{__version__}", style=f"bold {_HEADER_GRADIENT}")

    content = Group(logo_text, subtitle, version_text)

    console.print(
        Panel(
            content,
            border_style=_ACCENT_DIM,
            padding=(0, 2),
            expand=True,
        )
    )


def _print_brand_line() -> None:
    """Compact single-line brand for sub-commands."""
    console.print(
        f"  [{_ACCENT}]●[/{_ACCENT}]  "
        f"[bold {_VALUE}]AI Doctor[/bold {_VALUE}]  "
        f"[{_DIM}]v{__version__}[/{_DIM}]"
    )


def _print_footer() -> None:
    console.print()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    host = platform.node() or "unknown"

    console.print(Rule(style=_BORDER))
    console.print(
        f"  [{_DIM}]scan completed {ts}  ·  host: {host}  ·  ai-doctor v{__version__}[/{_DIM}]"
    )
    console.print(
        f"  [{_DIM}]run [bold]ai-doctor explain[/bold] for details  ·  "
        f"[bold]ai-doctor export -f json[/bold] to save  ·  "
        f"[bold]ai-doctor fix --dry-run[/bold] for remediation[/{_DIM}]"
    )
    console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# Quick Status Bar
# ═══════════════════════════════════════════════════════════════════════════════

def _print_quick_status(report: EnvironmentReport) -> None:
    """Compact status-pill row: GPU | CUDA | PyTorch."""
    console.print()

    items = [
        ("GPU",     report.gpu.status),
        ("CUDA",    report.cuda.status),
        ("PyTorch", report.torch.status),
    ]

    parts: list[str] = []
    for label, status in items:
        icon_char, fg, bg = _BADGE[status]
        tag = _STATUS_LABEL[status]
        parts.append(
            f"  [{_LABEL}]{label}[/{_LABEL}]  [{fg} on {bg}] {icon_char} {tag} [/{fg} on {bg}]  "
        )

    divider = f"[{_DIM}]│[/{_DIM}]"
    console.print("  " + divider.join(parts))
    console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# Detail Sections
# ═══════════════════════════════════════════════════════════════════════════════

def _make_section_table(rows: list[tuple[str, str, str]]) -> Table:
    """Create a consistently-styled key-value table."""
    t = Table(
        show_header=False,
        show_edge=False,
        show_lines=False,
        box=None,
        padding=(0, 2),
        expand=True,
    )
    t.add_column("key",    ratio=2, no_wrap=True)
    t.add_column("value",  ratio=4)
    t.add_column("status", ratio=2, justify="right")

    for row in rows:
        t.add_row(*row)

    return t


def _section_panel(title: str, icon: str, table: Table, note: str = "") -> Panel:
    """Wrap a table in a titled panel with optional note."""
    parts: list[Any] = [table]
    if note:
        parts.append(Text(""))
        parts.append(Text(f"  ℹ  {note}", style=f"italic {_DIM}"))

    return Panel(
        Group(*parts),
        title=f"[bold {_ACCENT}]  {icon}  {title}  [/bold {_ACCENT}]",
        title_align="left",
        border_style=_BORDER,
        padding=(1, 2),
        expand=True,
    )


def _print_sections(report: EnvironmentReport) -> None:
    """Render GPU, CUDA, PyTorch detail panels."""

    # ── GPU ──────────────────────────────────────────────────────
    gpu = report.gpu
    gpu_rows = [
        _kv("Device",        gpu.name,                                    status=gpu.status),
        _kv("Driver",        gpu.driver_version,                          status=gpu.status),
        _kv("VRAM",          f"{gpu.memory_total_mb} MiB" if gpu.memory_total_mb else "—"),
        _kv("Compute Cap.",  gpu.compute_capability),
    ]
    console.print(_section_panel("GPU", "⬡", _make_section_table(gpu_rows), gpu.error_message))
    console.print()

    # ── CUDA ─────────────────────────────────────────────────────
    cuda = report.cuda
    nvcc_label = f"[{_FG_OK}]Yes[/{_FG_OK}]" if cuda.nvcc_available else f"[{_FG_ERR}]No[/{_FG_ERR}]"
    cuda_rows = [
        _kv("Toolkit (nvcc)",   cuda.toolkit_version,  status=cuda.status),
        _kv("Runtime (torch)",  cuda.runtime_version),
        (f"[{_LABEL}]nvcc in PATH[/{_LABEL}]", nvcc_label, ""),
    ]
    console.print(_section_panel("CUDA", "⚡", _make_section_table(cuda_rows), cuda.error_message))
    console.print()

    # ── PyTorch ──────────────────────────────────────────────────
    t = report.torch
    cuda_avail_str = (
        f"[{_FG_OK}]True[/{_FG_OK}]" if t.cuda_available
        else f"[{_FG_ERR}]False[/{_FG_ERR}]"
    )
    torch_rows = [
        _kv("Version",         t.version,       status=t.status),
        _kv("CUDA built-in",   t.cuda_version),
        (f"[{_LABEL}]CUDA available[/{_LABEL}]", cuda_avail_str,
         _badge(Status.OK if t.cuda_available else Status.ERROR)),
        _kv("cuDNN",           t.cudnn_version),
    ]
    console.print(_section_panel("PyTorch", "🔥", _make_section_table(torch_rows), t.error_message))
    console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# Compatibility Verdict
# ═══════════════════════════════════════════════════════════════════════════════

def _print_compatibility_verdict(report: EnvironmentReport) -> None:
    if report.compatible:
        icon, fg, bg = "✓", _FG_OK, _BG_OK
        headline = "ALL CHECKS PASSED"
        border = "#065f46"
    else:
        icon, fg, bg = "✗", _FG_ERR, _BG_ERR
        headline = "ISSUES DETECTED"
        border = "#7f1d1d"

    badge_text = f"[bold {fg} on {bg}]  {icon}  {headline}  [/bold {fg} on {bg}]"
    notes = f"\n\n  [{_DIM}]{report.compatibility_notes}[/{_DIM}]" if report.compatibility_notes else ""

    console.print(
        Panel(
            badge_text + notes,
            border_style=border,
            padding=(1, 2),
            expand=True,
        )
    )
    console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# Recommendations
# ═══════════════════════════════════════════════════════════════════════════════

def _print_recommendations(report: EnvironmentReport) -> None:
    if not report.recommendations:
        return

    console.print(
        f"  [bold {_ACCENT}]RECOMMENDATIONS[/bold {_ACCENT}]"
    )
    console.print(Rule(style=_BORDER))
    console.print()

    for idx, rec in enumerate(report.recommendations, 1):
        icon_str = _icon(rec.severity)
        _, fg, _ = _BADGE[rec.severity]

        # Heading line
        console.print(f"  [{_DIM}]{idx:>2}.[/{_DIM}]  {icon_str}  [bold {fg}]{rec.summary}[/bold {fg}]")

        # Detail block
        if rec.details:
            console.print(f"       [{_DIM}]{rec.details}[/{_DIM}]")

        # Pip command — highlighted code block style
        if rec.pip_command:
            cmd_panel = Panel(
                f"[bold {_FG_OK}]$ {rec.pip_command}[/bold {_FG_OK}]",
                border_style=_ACCENT_DIM,
                padding=(0, 2),
                expand=False,
            )
            console.print(Padding(cmd_panel, (0, 0, 0, 7)))

        if idx < len(report.recommendations):
            console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# Explain view
# ═══════════════════════════════════════════════════════════════════════════════

def _build_explanation_text(report: EnvironmentReport) -> str:
    """Build a multi-paragraph human explanation."""
    lines: list[str] = []

    # GPU
    lines.append(f"[bold {_ACCENT}]GPU[/bold {_ACCENT}]")
    if report.gpu.status == Status.OK:
        lines.append(
            f"  You have an [{_FG_OK}]{report.gpu.name}[/{_FG_OK}] with "
            f"[bold]{report.gpu.memory_total_mb}[/bold] MiB VRAM and compute capability "
            f"[bold]{report.gpu.compute_capability}[/bold].  Driver "
            f"[bold]{report.gpu.driver_version}[/bold] is installed."
        )
    else:
        lines.append(
            f"  [{_FG_ERR}]No NVIDIA GPU was detected.[/{_FG_ERR}]  "
            f"[{_DIM}]nvidia-smi may not be in PATH, or no compatible GPU is present.[/{_DIM}]"
        )
    lines.append("")

    # CUDA
    lines.append(f"[bold {_ACCENT}]CUDA[/bold {_ACCENT}]")
    if report.cuda.status == Status.OK:
        lines.append(
            f"  Toolkit version [{_FG_OK}]{report.cuda.toolkit_version}[/{_FG_OK}] detected "
            f"via nvcc.  PyTorch reports runtime [bold]{report.cuda.runtime_version}[/bold]."
        )
    elif report.cuda.status == Status.WARNING:
        lines.append(f"  [{_FG_WARN}]{report.cuda.error_message}[/{_FG_WARN}]")
    else:
        lines.append(
            f"  [{_FG_ERR}]No CUDA toolkit detected.[/{_FG_ERR}]  "
            f"[{_DIM}]PyTorch wheels bundle the CUDA runtime — a system toolkit is optional.[/{_DIM}]"
        )
    lines.append("")

    # PyTorch
    lines.append(f"[bold {_ACCENT}]PyTorch[/bold {_ACCENT}]")
    if report.torch.installed:
        avail_str = (
            f"[{_FG_OK}]True[/{_FG_OK}]" if report.torch.cuda_available
            else f"[{_FG_ERR}]False[/{_FG_ERR}]"
        )
        lines.append(
            f"  Version [{_FG_OK}]{report.torch.version}[/{_FG_OK}] "
            f"(CUDA {report.torch.cuda_version}).  "
            f"torch.cuda.is_available() → {avail_str}"
        )
    else:
        lines.append(f"  [{_FG_ERR}]Not installed.[/{_FG_ERR}]")
    lines.append("")

    # Notes
    if report.compatibility_notes:
        lines.append(f"[bold {_ACCENT}]Notes[/bold {_ACCENT}]")
        lines.append(f"  [{_DIM}]{report.compatibility_notes}[/{_DIM}]")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# JSON Serialization
# ═══════════════════════════════════════════════════════════════════════════════

def _report_to_dict(report: EnvironmentReport) -> dict[str, Any]:
    """Convert the report to a plain dict for JSON export."""
    return {
        "meta": {
            "tool": "ai-doctor",
            "version": __version__,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "host": platform.node(),
        },
        "gpu": {
            "name": report.gpu.name,
            "driver_version": report.gpu.driver_version,
            "memory_total_mb": report.gpu.memory_total_mb,
            "compute_capability": report.gpu.compute_capability,
            "status": report.gpu.status.value,
            "error": report.gpu.error_message,
        },
        "cuda": {
            "toolkit_version": report.cuda.toolkit_version,
            "runtime_version": report.cuda.runtime_version,
            "nvcc_available": report.cuda.nvcc_available,
            "status": report.cuda.status.value,
            "error": report.cuda.error_message,
        },
        "pytorch": {
            "version": report.torch.version,
            "cuda_version": report.torch.cuda_version,
            "cuda_available": report.torch.cuda_available,
            "cudnn_version": report.torch.cudnn_version,
            "installed": report.torch.installed,
            "status": report.torch.status.value,
            "error": report.torch.error_message,
        },
        "compatible": report.compatible,
        "compatibility_notes": report.compatibility_notes,
        "recommendations": [
            {
                "summary": r.summary,
                "pip_command": r.pip_command,
                "severity": r.severity.value,
                "details": r.details,
            }
            for r in report.recommendations
        ],
    }
