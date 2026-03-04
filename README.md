<![CDATA[<div align="center">

```
     _    ___     ____             _
    / \  |_ _|   |  _ \  ___   ___| |_ ___  _ __
   / _ \  | |    | | | |/ _ \ / __| __/ _ \| '__|
  / ___ \ | |    | |_| | (_) | (__| || (_) | |
 /_/   \_\___|   |____/ \___/ \___|\__\___/|_|
```

**GPU · CUDA · PyTorch Environment Diagnostics**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776ab.svg?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e.svg?style=flat-square)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?style=flat-square)](https://github.com/astral-sh/ruff)

</div>

---

**AI Doctor** is a production-grade CLI tool that detects GPU, CUDA, and PyTorch environment issues, checks version compatibility, and recommends fixes — all with a premium terminal UI.

## ✨ Features

- 🖥️ **GPU Detection** — Reads device name, driver, VRAM, and compute capability via `nvidia-smi`
- ⚡ **CUDA Detection** — Checks toolkit (`nvcc`) and runtime (`torch.version.cuda`) versions
- 🔥 **PyTorch Detection** — Reads version, CUDA build tag, cuDNN, and `torch.cuda.is_available()`
- 🔗 **Compatibility Engine** — Driver → CUDA → PyTorch matrix with automatic recommendations
- 🩹 **Auto-Fix** — Generates and optionally executes `pip install` commands to resolve mismatches
- 📤 **JSON Export** — Machine-readable reports with metadata (timestamp, hostname, version)
- 🎨 **Premium CLI** — Rich-powered output with ASCII branding, status badges, and structured panels

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/ai-doctor.git
cd ai-doctor

# Install in editable mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## 🚀 Usage

```bash
# Full environment diagnostic
ai-doctor check

# Human-friendly explanation
ai-doctor explain

# Show fix commands (dry run)
ai-doctor fix --dry-run

# Apply fixes
ai-doctor fix

# Export as JSON
ai-doctor export --format json

# Export to file
ai-doctor export --format json --output report.json

# Version
ai-doctor --version
```

> **Tip:** If `ai-doctor` gives a permission error, use `python -m ai_doctor` instead.

## 🖼️ Output Preview

### `ai-doctor check`

```
╭──────────────────────────────────────────────────────────╮
│      _    ___     ____             _                     │
│     / \  |_ _|   |  _ \  ___   ___| |_ ___  _ __        │
│    / _ \  | |    | | | |/ _ \ / __| __/ _ \| '__|       │
│   / ___ \ | |    | |_| | (_) | (__| || (_) | |          │
│  /_/   \_\___|   |____/ \___/ \___|\__\___/|_|          │
│   GPU · CUDA · PyTorch  Environment Diagnostics         │
│   v1.0.0                                                │
╰──────────────────────────────────────────────────────────╯

  GPU  ✓ PASS  │  CUDA  ✓ PASS  │  PyTorch  ✓ PASS

╭─  ⬡  GPU  ──────────────────────────────────────────────╮
│   Device          NVIDIA GeForce RTX 3050      ✓ PASS   │
│   Driver          560.94                       ✓ PASS   │
│   VRAM            8192 MiB                              │
│   Compute Cap.    8.6                                   │
╰──────────────────────────────────────────────────────────╯

╭─  ⚡  CUDA  ─────────────────────────────────────────────╮
│   Toolkit (nvcc)  12.6                         ✓ PASS   │
│   Runtime (torch) 12.6                                  │
│   nvcc in PATH    Yes                                   │
╰──────────────────────────────────────────────────────────╯

╭─  🔥  PyTorch  ──────────────────────────────────────────╮
│   Version         2.8.0+cu126                  ✓ PASS   │
│   CUDA built-in   12.6                                  │
│   CUDA available  True                         ✓ PASS   │
│   cuDNN           91.0.2                                │
╰──────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────╮
│  ✓  ALL CHECKS PASSED                                   │
│  Driver 560.94 supports up to CUDA 12.6.                │
╰──────────────────────────────────────────────────────────╯

  RECOMMENDATIONS
────────────────────────────────────────────────────────────
  1.  ✓  Recommended: PyTorch 2.6.0 with CUDA 12.4
      ╭────────────────────────────────────────────────────╮
      │ $ pip install torch==2.6.0 --index-url             │
      │   https://download.pytorch.org/whl/cu124           │
      ╰────────────────────────────────────────────────────╯
```

### `ai-doctor fix --dry-run`

```
╭──────────────────────────────────────────────────────────╮
│  ▶  DRY RUN                                             │
│  The following commands will be shown but not executed.  │
╰──────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────╮
│  #   Command                                            │
│  1   $ pip install torch==2.6.0 --index-url             │
│        https://download.pytorch.org/whl/cu124           │
╰──────────────────────────────────────────────────────────╯

  Remove --dry-run to execute:  ai-doctor fix
```

## 🏗️ Project Structure

```
ai_doctor/
├── __init__.py          # Package version
├── __main__.py          # python -m ai_doctor entry point
├── models.py            # Frozen dataclasses & Status enum
├── gpu.py               # GPU detection via nvidia-smi
├── cuda.py              # CUDA detection via nvcc + torch
├── torch_check.py       # PyTorch version & CUDA detection
├── compatibility.py     # Driver→CUDA→PyTorch matrix engine
├── reporter.py          # Rich-powered rendering & JSON export
├── fixer.py             # Fix command generation & execution
└── cli.py               # Typer CLI commands (thin orchestration)
```

## 🧠 Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────────┐
│  gpu.py  │     │ cuda.py  │     │ torch_check  │   Detection Layer
└────┬─────┘     └────┬─────┘     └──────┬───────┘
     │                │                   │
     └───────────┬────┴──────────────────┘
                 ▼
        ┌────────────────┐
        │ compatibility  │                           Analysis Layer
        └───────┬────────┘
                │
        ┌───────┴────────┐
        │  models.py     │                           Data Layer
        │ (dataclasses)  │
        └───────┬────────┘
                │
     ┌──────────┼──────────┐
     ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────┐
│ reporter │ │ fixer  │ │  cli   │                   Presentation Layer
└──────────┘ └────────┘ └────────┘
```

## 🔧 Compatibility Matrix

The tool includes a built-in compatibility matrix mapping:

| NVIDIA Driver | Max CUDA | Recommended PyTorch |
|--------------|----------|-------------------|
| ≥ 560.00     | 12.6     | 2.6.0 (cu124)     |
| ≥ 550.54     | 12.4     | 2.6.0 (cu124)     |
| ≥ 535.54     | 12.2     | 2.5.1 (cu121)     |
| ≥ 525.60     | 12.0     | 2.5.1 (cu121)     |
| ≥ 520.61     | 11.8     | 2.4.1 (cu118)     |
| ≥ 515.43     | 11.7     | 2.0.1 (cu117)     |

## 🧪 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Type checking
mypy ai_doctor/

# Linting
ruff check ai_doctor/

# Run tests
pytest
```

## 📄 License

[MIT](LICENSE)
]]>
