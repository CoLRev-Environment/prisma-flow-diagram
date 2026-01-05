"""Package for py-prisma."""

from dataclasses import asdict
from pathlib import Path

from .loader import load_status_from_records
from .loader import PrismaStatus, Prisma2020New, Prisma2020Updated
from .prisma import plot_prisma2020_new, plot_prisma2020_updated

__author__ = "Gerit Wagner"
__email__ = "gerit.wagner@uni-bamberg.de"

__all__ = [
    "PrismaStatus",
    "load_status_from_records",
    "plot_prisma2020",
]


# -------------------------
# Plot convenience wrapper
# -------------------------


def plot_prisma_from_records(
    *,
    records_path: str | Path = "data/records.bib",
    output_path: str | Path = "prisma.png",
    show: bool = False,
    prior_reviews: list[str] | None = None,
    other_methods: list[str] | None = None,
) -> None:
    params = load_status_from_records(
        records_path,
        prior_reviews=prior_reviews,
        other_methods=other_methods,
    )

    if isinstance(params, Prisma2020New):
        plot_prisma2020_new(
            **asdict(params),
            filename=str(output_path),
            show=show,
        )
        return

    if isinstance(params, Prisma2020Updated):
        plot_prisma2020_updated(
            **asdict(params),
            filename=str(output_path),
            show=show,
        )
        return

    raise TypeError(f"Unexpected params type: {type(params)!r}")
