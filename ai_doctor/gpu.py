"""GPU detection via nvidia-smi subprocess calls."""

from __future__ import annotations

import re
import subprocess
from typing import Optional

from ai_doctor.models import GPUInfo, Status


def _run_nvidia_smi(args: list[str] | None = None) -> Optional[str]:
    """Execute nvidia-smi with optional arguments and return stdout."""
    cmd = ["nvidia-smi"]
    if args:
        cmd.extend(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return None


def _parse_driver_version(raw: str) -> str:
    """Extract the driver version string from nvidia-smi output."""
    match = re.search(r"Driver Version:\s*([\d.]+)", raw)
    return match.group(1) if match else "Unknown"


def _parse_gpu_name(raw: str) -> str:
    """Extract the GPU product name from nvidia-smi output."""
    match = re.search(r"\|\s+\d+\s+([\w\s\-/]+?)\s+(On|Off)\s+\|", raw)
    if match:
        return match.group(1).strip()
    # Fallback: try the query-based approach result
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("+") and not stripped.startswith("|") and not stripped.startswith("="):
            return stripped
    return "Unknown"


def _parse_memory_total(raw: str) -> int:
    """Extract total GPU memory in MiB from nvidia-smi output."""
    match = re.search(r"(\d+)\s*MiB\s*\|", raw)
    # nvidia-smi shows "Used / Total" — grab the second occurrence (total)
    matches = re.findall(r"(\d+)\s*MiB", raw)
    if len(matches) >= 2:
        return int(matches[1])
    if matches:
        return int(matches[0])
    return 0


def _query_gpu_name() -> str:
    """Use nvidia-smi --query-gpu to get GPU name reliably."""
    output = _run_nvidia_smi(
        ["--query-gpu=gpu_name", "--format=csv,noheader,nounits"]
    )
    if output:
        return output.splitlines()[0].strip()
    return "Unknown"


def _query_memory_total() -> int:
    """Use nvidia-smi --query-gpu to get total memory in MiB."""
    output = _run_nvidia_smi(
        ["--query-gpu=memory.total", "--format=csv,noheader,nounits"]
    )
    if output:
        try:
            return int(output.splitlines()[0].strip())
        except ValueError:
            return 0
    return 0


def _query_compute_capability() -> str:
    """Use nvidia-smi to get compute capability."""
    output = _run_nvidia_smi(
        ["--query-gpu=compute_cap", "--format=csv,noheader,nounits"]
    )
    if output:
        return output.splitlines()[0].strip()
    return "Unknown"


def detect_gpu() -> GPUInfo:
    """Detect NVIDIA GPU information.

    Returns a GPUInfo dataclass with status set to OK when a GPU is found,
    or NOT_FOUND / ERROR when detection fails.
    """
    raw_output = _run_nvidia_smi()

    if raw_output is None:
        return GPUInfo(
            status=Status.NOT_FOUND,
            error_message="nvidia-smi not found or not responding. No NVIDIA GPU detected.",
        )

    driver_version = _parse_driver_version(raw_output)

    # Prefer query-based parsing for reliability
    gpu_name = _query_gpu_name()
    if gpu_name == "Unknown":
        gpu_name = _parse_gpu_name(raw_output)

    memory_total = _query_memory_total()
    if memory_total == 0:
        memory_total = _parse_memory_total(raw_output)

    compute_cap = _query_compute_capability()

    return GPUInfo(
        name=gpu_name,
        driver_version=driver_version,
        memory_total_mb=memory_total,
        compute_capability=compute_cap,
        status=Status.OK,
    )
