"""Shared data models used across modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    """Health status of a detected component."""

    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class GPUInfo:
    """Information about the detected NVIDIA GPU."""

    name: str = "Unknown"
    driver_version: str = "Unknown"
    memory_total_mb: int = 0
    compute_capability: str = "Unknown"
    status: Status = Status.NOT_FOUND
    error_message: str = ""


@dataclass(frozen=True)
class CUDAInfo:
    """Information about the detected CUDA installation."""

    toolkit_version: str = "Unknown"
    runtime_version: str = "Unknown"
    nvcc_available: bool = False
    status: Status = Status.NOT_FOUND
    error_message: str = ""


@dataclass(frozen=True)
class TorchInfo:
    """Information about the detected PyTorch installation."""

    version: str = "Unknown"
    cuda_version: str = "Unknown"
    cuda_available: bool = False
    cudnn_version: str = "Unknown"
    installed: bool = False
    status: Status = Status.NOT_FOUND
    error_message: str = ""


@dataclass(frozen=True)
class Recommendation:
    """A recommended action to fix a detected issue."""

    summary: str
    pip_command: str = ""
    severity: Status = Status.WARNING
    details: str = ""


@dataclass
class EnvironmentReport:
    """Aggregated environment diagnostics report."""

    gpu: GPUInfo = field(default_factory=GPUInfo)
    cuda: CUDAInfo = field(default_factory=CUDAInfo)
    torch: TorchInfo = field(default_factory=TorchInfo)
    recommendations: list[Recommendation] = field(default_factory=list)
    compatible: bool = False
    compatibility_notes: str = ""
