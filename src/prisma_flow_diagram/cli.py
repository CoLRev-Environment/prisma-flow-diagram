from __future__ import annotations

import argparse
from pathlib import Path

from py_prisma import plot_prisma_from_records


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

    plot_prisma_from_records(output_path=args.output, show=args.show)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
