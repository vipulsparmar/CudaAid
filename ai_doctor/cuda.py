"""CUDA toolkit detection via nvcc and optional torch.version.cuda."""

from __future__ import annotations

import re
import subprocess

from ai_doctor.models import CUDAInfo, Status


def _detect_nvcc_version() -> tuple[bool, str]:
    """Run ``nvcc --version`` and extract the CUDA version string.

    Returns:
        (available, version_string)
    """
    try:
        result = subprocess.run(
            ["nvcc", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False, "Unknown"

        match = re.search(r"release\s+([\d.]+)", result.stdout)
        if match:
            return True, match.group(1)
        return True, "Unknown"

    except FileNotFoundError:
        return False, "Unknown"
    except subprocess.TimeoutExpired:
        return False, "Unknown"


def _detect_torch_cuda_version() -> str:
    """Attempt to read ``torch.version.cuda`` if PyTorch is installed."""
    try:
        import torch  # type: ignore[import-untyped]

        cuda_ver: str | None = getattr(torch.version, "cuda", None)
        return cuda_ver if cuda_ver else "Unknown"
    except ImportError:
        return "Unknown"


def detect_cuda() -> CUDAInfo:
    """Detect CUDA toolkit information from nvcc and/or PyTorch.

    Returns a CUDAInfo dataclass with the best information available.
    """
    nvcc_available, toolkit_version = _detect_nvcc_version()
    runtime_version = _detect_torch_cuda_version()

    if not nvcc_available and runtime_version == "Unknown":
        return CUDAInfo(
            status=Status.NOT_FOUND,
            error_message="No CUDA toolkit detected (nvcc not found, torch.version.cuda unavailable).",
        )

    # Determine overall status
    status = Status.OK
    error_message = ""

    if not nvcc_available:
        status = Status.WARNING
        error_message = (
            "nvcc not found in PATH. CUDA toolkit may not be fully installed. "
            "Runtime version detected via PyTorch."
        )

    return CUDAInfo(
        toolkit_version=toolkit_version,
        runtime_version=runtime_version,
        nvcc_available=nvcc_available,
        status=status,
        error_message=error_message,
    )
