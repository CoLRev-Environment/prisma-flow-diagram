from __future__ import annotations
"""Package for py-prisma."""

__author__ = "Gerit Wagner"
__email__ = "gerit.wagner@uni-bamberg.de"

from .loader import PrismaStatus, load_status_from_records
from .plotter import plot_simple_prisma
from pathlib import Path

from .loader import load_status_from_records
from .plotter import plot_simple_prisma

__all__ = [
    "PrismaStatus",
    "load_status_from_records",
    "plot_simple_prisma",
]

def plot_prisma_from_records(
    *,
    records_path: str | Path = "data/records.bib",
    output_path: str | Path = "prisma.png",
    show: bool = False,
) -> None:
    status = load_status_from_records(records_path)
    plot_simple_prisma(status, filename=output_path, show=show)
