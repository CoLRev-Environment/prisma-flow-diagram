from __future__ import annotations

import argparse
from pathlib import Path

from .loader import load_status_from_records
from .plotter import plot_simple_prisma


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prisma-from-records",
        description="Generate a PRISMA-style flow diagram from a CoLRev records.bib file.",
    )
    p.add_argument(
        "records",
        type=Path,
        help="Path to CoLRev records file (e.g., data/records.bib).",
    )
    p.add_argument(
        "output",
        type=Path,
        help="Output path (png/svg/pdf/... inferred from extension).",
    )
    p.add_argument(
        "--show",
        action="store_true",
        help="Show the figure in a window (in addition to saving).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.records.exists():
        raise FileNotFoundError(f"Records file not found: {args.records}")

    status = load_status_from_records(args.records)
    plot_simple_prisma(status, filename=args.output, show=args.show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
