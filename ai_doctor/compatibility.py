"""Compatibility matrix and recommendation engine.

Maps NVIDIA driver versions → maximum supported CUDA versions,
and CUDA versions → recommended PyTorch builds.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_doctor.models import (
    CUDAInfo,
    EnvironmentReport,
    GPUInfo,
    Recommendation,
    Status,
    TorchInfo,
)


# ---------------------------------------------------------------------------
# Compatibility data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CUDACompat:
    """Maps a minimum driver version to the maximum CUDA toolkit it supports."""

    min_driver: str
    max_cuda: str


@dataclass(frozen=True)
class TorchBuild:
    """A known stable PyTorch build and its matching CUDA tag."""

    torch_version: str
    cuda_tag: str  # e.g. "cu118", "cu121", "cu124"
    cuda_version: str  # e.g. "11.8", "12.1", "12.4"
    index_url: str


# Source: https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/
DRIVER_CUDA_MATRIX: list[CUDACompat] = [
    CUDACompat("560.00", "12.6"),
    CUDACompat("555.42", "12.5"),
    CUDACompat("550.54", "12.4"),
    CUDACompat("545.23", "12.3"),
    CUDACompat("535.54", "12.2"),
    CUDACompat("530.30", "12.1"),
    CUDACompat("525.60", "12.0"),
    CUDACompat("520.61", "11.8"),
    CUDACompat("515.43", "11.7"),
    CUDACompat("510.39", "11.6"),
    CUDACompat("495.29", "11.5"),
    CUDACompat("470.42", "11.4"),
    CUDACompat("465.19", "11.3"),
    CUDACompat("460.32", "11.2"),
    CUDACompat("455.23", "11.1"),
    CUDACompat("450.36", "11.0"),
]

# Stable PyTorch builds (latest per CUDA tag as of early 2026)
TORCH_BUILDS: list[TorchBuild] = [
    TorchBuild("2.6.0", "cu124", "12.4", "https://download.pytorch.org/whl/cu124"),
    TorchBuild("2.5.1", "cu124", "12.4", "https://download.pytorch.org/whl/cu124"),
    TorchBuild("2.5.1", "cu121", "12.1", "https://download.pytorch.org/whl/cu121"),
    TorchBuild("2.4.1", "cu124", "12.4", "https://download.pytorch.org/whl/cu124"),
    TorchBuild("2.4.1", "cu121", "12.1", "https://download.pytorch.org/whl/cu121"),
    TorchBuild("2.4.1", "cu118", "11.8", "https://download.pytorch.org/whl/cu118"),
    TorchBuild("2.3.1", "cu121", "12.1", "https://download.pytorch.org/whl/cu121"),
    TorchBuild("2.3.1", "cu118", "11.8", "https://download.pytorch.org/whl/cu118"),
    TorchBuild("2.2.2", "cu121", "12.1", "https://download.pytorch.org/whl/cu121"),
    TorchBuild("2.2.2", "cu118", "11.8", "https://download.pytorch.org/whl/cu118"),
    TorchBuild("2.1.2", "cu121", "12.1", "https://download.pytorch.org/whl/cu121"),
    TorchBuild("2.1.2", "cu118", "11.8", "https://download.pytorch.org/whl/cu118"),
    TorchBuild("2.0.1", "cu118", "11.8", "https://download.pytorch.org/whl/cu118"),
    TorchBuild("2.0.1", "cu117", "11.7", "https://download.pytorch.org/whl/cu117"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _version_tuple(ver: str) -> tuple[int, ...]:
    """Convert a dotted version string to an integer tuple for comparison."""
    parts: list[int] = []
    for segment in ver.split("."):
        try:
            parts.append(int(segment))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def max_cuda_for_driver(driver_version: str) -> str | None:
    """Return the highest CUDA version supported by the given driver."""
    driver_t = _version_tuple(driver_version)
    for compat in DRIVER_CUDA_MATRIX:
        if driver_t >= _version_tuple(compat.min_driver):
            return compat.max_cuda
    return None


def best_torch_for_cuda(cuda_version: str) -> TorchBuild | None:
    """Return the latest stable PyTorch build compatible with *cuda_version*."""
    cuda_t = _version_tuple(cuda_version)
    for build in TORCH_BUILDS:
        if _version_tuple(build.cuda_version) <= cuda_t:
            return build
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse(gpu: GPUInfo, cuda: CUDAInfo, torch_info: TorchInfo) -> EnvironmentReport:
    """Run the full compatibility analysis and return an EnvironmentReport."""
    recommendations: list[Recommendation] = []
    compatible = True
    notes_parts: list[str] = []

    # --- GPU checks ----------------------------------------------------------
    if gpu.status == Status.NOT_FOUND:
        compatible = False
        recommendations.append(
            Recommendation(
                summary="No NVIDIA GPU detected.",
                details="Install an NVIDIA GPU or check that nvidia-smi is accessible in PATH.",
                severity=Status.ERROR,
            )
        )

    # --- Driver → CUDA ceiling -----------------------------------------------
    max_cuda: str | None = None
    if gpu.status == Status.OK:
        max_cuda = max_cuda_for_driver(gpu.driver_version)
        if max_cuda:
            notes_parts.append(
                f"Driver {gpu.driver_version} supports up to CUDA {max_cuda}."
            )
        else:
            compatible = False
            recommendations.append(
                Recommendation(
                    summary="Driver version is too old for any known CUDA release.",
                    details=f"Detected driver {gpu.driver_version}. Update to ≥450.36.",
                    severity=Status.ERROR,
                )
            )

    # --- CUDA checks ---------------------------------------------------------
    if cuda.status == Status.NOT_FOUND:
        recommendations.append(
            Recommendation(
                summary="CUDA toolkit not found.",
                details=(
                    "Install the CUDA toolkit from https://developer.nvidia.com/cuda-downloads "
                    "or install a CUDA-enabled PyTorch wheel (toolkit bundled)."
                ),
                severity=Status.WARNING,
            )
        )
    elif cuda.status == Status.WARNING:
        recommendations.append(
            Recommendation(
                summary="nvcc not in PATH.",
                details=cuda.error_message,
                severity=Status.WARNING,
            )
        )

    # Check toolkit vs. driver ceiling
    if max_cuda and cuda.toolkit_version != "Unknown":
        if _version_tuple(cuda.toolkit_version) > _version_tuple(max_cuda):
            compatible = False
            recommendations.append(
                Recommendation(
                    summary="Installed CUDA toolkit exceeds driver support.",
                    details=(
                        f"CUDA {cuda.toolkit_version} requires a newer driver. "
                        f"Your driver ({gpu.driver_version}) supports up to CUDA {max_cuda}."
                    ),
                    severity=Status.ERROR,
                )
            )

    # --- PyTorch checks ------------------------------------------------------
    if not torch_info.installed:
        recommendations.append(
            Recommendation(
                summary="PyTorch is not installed.",
                severity=Status.WARNING,
            )
        )
    else:
        # Check for CUDA mismatch inside PyTorch build tag
        torch_cuda = torch_info.cuda_version
        if torch_cuda and torch_cuda not in ("N/A", "Unknown"):
            if max_cuda and _version_tuple(torch_cuda) > _version_tuple(max_cuda):
                compatible = False
                recommendations.append(
                    Recommendation(
                        summary="PyTorch CUDA version exceeds driver capability.",
                        details=(
                            f"PyTorch was built for CUDA {torch_cuda}, but your driver "
                            f"supports up to CUDA {max_cuda}."
                        ),
                        severity=Status.ERROR,
                    )
                )

        if not torch_info.cuda_available and torch_cuda not in ("N/A", "None"):
            compatible = False
            recommendations.append(
                Recommendation(
                    summary="torch.cuda.is_available() is False.",
                    details=(
                        "PyTorch cannot access the GPU. Possible causes: "
                        "driver/toolkit mismatch, missing libcuda, or WSL limitations."
                    ),
                    severity=Status.ERROR,
                )
            )

    # --- Build a recommended pip command -------------------------------------
    effective_cuda = max_cuda
    if effective_cuda is None and cuda.toolkit_version != "Unknown":
        effective_cuda = cuda.toolkit_version
    if effective_cuda is None and cuda.runtime_version != "Unknown":
        effective_cuda = cuda.runtime_version

    if effective_cuda:
        recommended_build = best_torch_for_cuda(effective_cuda)
        if recommended_build:
            pip_cmd = (
                f"pip install torch=={recommended_build.torch_version} "
                f"--index-url {recommended_build.index_url}"
            )
            recommendations.append(
                Recommendation(
                    summary=(
                        f"Recommended: PyTorch {recommended_build.torch_version} "
                        f"with CUDA {recommended_build.cuda_version}"
                    ),
                    pip_command=pip_cmd,
                    severity=Status.OK,
                )
            )
            notes_parts.append(
                f"Best match: torch {recommended_build.torch_version} "
                f"({recommended_build.cuda_tag})."
            )

    return EnvironmentReport(
        gpu=gpu,
        cuda=cuda,
        torch=torch_info,
        recommendations=recommendations,
        compatible=compatible,
        compatibility_notes=" ".join(notes_parts),
    )
