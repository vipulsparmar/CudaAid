"""PyTorch installation detection."""

from __future__ import annotations

from ai_doctor.models import Status, TorchInfo


def detect_torch() -> TorchInfo:
    """Detect PyTorch installation details.

    Attempts to import torch and read version, CUDA availability,
    and cuDNN version.  Returns TorchInfo with ``installed=False``
    when PyTorch is not importable.
    """
    try:
        import torch  # type: ignore[import-untyped]
    except ImportError:
        return TorchInfo(
            status=Status.NOT_FOUND,
            error_message="PyTorch is not installed.",
        )

    version: str = getattr(torch, "__version__", "Unknown")

    cuda_version: str = "N/A"
    cuda_attr = getattr(torch.version, "cuda", None)
    if cuda_attr is not None:
        cuda_version = str(cuda_attr)

    cuda_available: bool = False
    try:
        cuda_available = torch.cuda.is_available()
    except Exception:
        pass

    cudnn_version: str = "N/A"
    try:
        cudnn_ver = torch.backends.cudnn.version()  # type: ignore[attr-defined]
        if cudnn_ver:
            major = cudnn_ver // 1000
            minor = (cudnn_ver % 1000) // 100
            patch = cudnn_ver % 100
            cudnn_version = f"{major}.{minor}.{patch}"
    except Exception:
        pass

    # Determine status
    status = Status.OK
    error_message = ""

    if not cuda_available and cuda_version != "N/A":
        status = Status.WARNING
        error_message = (
            "PyTorch was built with CUDA support but torch.cuda.is_available() returned False. "
            "Check driver / toolkit compatibility."
        )
    elif cuda_version == "N/A":
        status = Status.WARNING
        error_message = "PyTorch is installed as CPU-only build."

    return TorchInfo(
        version=version,
        cuda_version=cuda_version,
        cuda_available=cuda_available,
        cudnn_version=cudnn_version,
        installed=True,
        status=status,
        error_message=error_message,
    )
