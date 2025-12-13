#!/usr/bin/env python3
"""
Generate a PRISMA 2020 flow diagram from a YAML file.

Usage:
    python prisma_from_yaml.py prisma.yaml prisma_chart.png
"""

import sys
import textwrap
from pathlib import Path

import yaml
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch


def wrap(text, width=40):
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def draw_box(ax, x, y, w, h, text, fc="white", ec="black", fontsize=9, weight="normal"):
    """Draw a rectangle with centered text."""
    rect = Rectangle((x, y), w, h, linewidth=1, edgecolor=ec, facecolor=fc)
    ax.add_patch(rect)
    ax.text(
        x + w / 2,
        y + h / 2,
        wrap(text),
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight=weight,
    )
    return rect


def draw_arrow(ax, x1, y1, x2, y2):
    """Draw a straight arrow from (x1, y1) to (x2, y2)."""
    arrow = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle="->",
        mutation_scale=12,
        linewidth=1,
    )
    ax.add_patch(arrow)


def load_prisma_data(path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["prisma_2020"]


def build_texts(p):
    """Build the box texts from the YAML dict."""
    id_ = p["identification"]
    scr = p["screening"]
    inc = p["included"]

    # identification: records identified
    box_identified = (
        "Records identified from:\n"
        f"Databases (n = {id_['databases']['total']})\n"
        f"Registers (n = {id_['registers']['total']})"
    )

    # removed before screening
    rbs = id_["removed_before_screening"]
    box_removed = (
        "Records removed before screening:\n"
        f"Duplicate records removed (n = {rbs['duplicates']})\n"
        f"Records marked as ineligible by\n"
        f"automation tools (n = {rbs['automation']})\n"
        f"Records removed for other reasons (n = {rbs['other']})"
    )

    # screening boxes
    box_screened = f"Records screened (n = {scr['records_screened']})"
    box_excluded = f"Records excluded (n = {scr['records_excluded']})"

    box_sought = f"Reports sought for retrieval (n = {scr['reports_sought_for_retrieval']})"
    box_not_retrieved = f"Reports not retrieved (n = {scr['reports_not_retrieved']})"

    box_assessed = f"Reports assessed for eligibility (n = {scr['reports_assessed_for_eligibility']})"

    # reports excluded with reasons
    reasons = scr["reports_excluded"].get("by_reason", [])
    reason_lines = []
    for r in reasons:
        reason_lines.append(f"{r['reason']} (n = {r['n']})")
    reasons_text = "\n".join(reason_lines) if reason_lines else "None"
    box_reports_excluded = "Reports excluded:\n" + reasons_text

    # included
    box_included = (
        "Studies included in review\n"
        f"(n = {inc['studies_included_in_review']})\n\n"
        "Reports of included studies\n"
        f"(n = {inc['reports_of_included_studies']})"
    )

    return {
        "ident_header": "Identification of studies via databases and registers",
        "box_identified": box_identified,
        "box_removed": box_removed,
        "box_screened": box_screened,
        "box_excluded": box_excluded,
        "box_sought": box_sought,
        "box_not_retrieved": box_not_retrieved,
        "box_assessed": box_assessed,
        "box_reports_excluded": box_reports_excluded,
        "box_included": box_included,
    }


def plot_prisma(prisma_yaml_path, output_path):
    prisma = load_prisma_data(prisma_yaml_path)
    texts = build_texts(prisma)

    # Create figure
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis("off")

    # --- Header (yellow bar) ---
    draw_box(
        ax,
        x=1,
        y=12.5,
        w=8,
        h=1,
        text=texts["ident_header"],
        fc="#ffd966",  # light yellow
        fontsize=11,
        weight="bold",
    )

    # Coordinates/size for main column boxes
    box_w = 4.5
    box_h = 1.1
    center_x = 3.25

    # 1) Records identified (left column)
    b1 = draw_box(
        ax,
        x=center_x,
        y=10.8,
        w=box_w,
        h=box_h,
        text=texts["box_identified"],
    )

    # 1b) Removed before screening (right of b1)
    draw_box(
        ax,
        x=center_x + box_w + 0.75,
        y=10.8,
        w=4,
        h=box_h,
        text=texts["box_removed"],
    )

    # Arrow down to Records screened
    draw_arrow(
        ax,
        x1=center_x + box_w / 2,
        y1=10.8,
        x2=center_x + box_w / 2,
        y2=10.8 - 0.4,
    )

    # 2) Records screened
    b2_y = 9.0
    draw_box(
        ax,
        x=center_x,
        y=b2_y,
        w=box_w,
        h=box_h,
        text=texts["box_screened"],
    )

    # 2b) Records excluded (right)
    draw_box(
        ax,
        x=center_x + box_w + 0.75,
        y=b2_y,
        w=4,
        h=box_h,
        text=texts["box_excluded"],
    )

    draw_arrow(
        ax,
        x1=center_x + box_w / 2,
        y1=b2_y,
        x2=center_x + box_w / 2,
        y2=b2_y - 0.4,
    )

    # 3) Reports sought for retrieval
    b3_y = 7.2
    draw_box(
        ax,
        x=center_x,
        y=b3_y,
        w=box_w,
        h=box_h,
        text=texts["box_sought"],
    )

    # 3b) Reports not retrieved
    draw_box(
        ax,
        x=center_x + box_w + 0.75,
        y=b3_y,
        w=4,
        h=box_h,
        text=texts["box_not_retrieved"],
    )

    draw_arrow(
        ax,
        x1=center_x + box_w / 2,
        y1=b3_y,
        x2=center_x + box_w / 2,
        y2=b3_y - 0.4,
    )

    # 4) Reports assessed for eligibility
    b4_y = 5.4
    draw_box(
        ax,
        x=center_x,
        y=b4_y,
        w=box_w,
        h=box_h,
        text=texts["box_assessed"],
    )

    # 4b) Reports excluded with reasons
    draw_box(
        ax,
        x=center_x + box_w + 0.75,
        y=b4_y,
        w=4,
        h=box_h + 0.6,  # a bit taller
        text=texts["box_reports_excluded"],
    )

    draw_arrow(
        ax,
        x1=center_x + box_w / 2,
        y1=b4_y,
        x2=center_x + box_w / 2,
        y2=b4_y - 0.4,
    )

    # 5) Studies included
    b5_y = 3.2
    draw_box(
        ax,
        x=center_x,
        y=b5_y,
        w=box_w,
        h=box_h + 0.4,
        text=texts["box_included"],
        fc="#d9ead3",  # light green
        weight="bold",
    )

    # Optional side labels ("Identification", "Screening", "Included")
    stage_w = 1.2
    stage_h = 2.6

    draw_box(
        ax,
        x=0.4,
        y=10.4,
        w=stage_w,
        h=stage_h,
        text="Identification",
        fc="#c9daf8",
        weight="bold",
        fontsize=9,
    )
    draw_box(
        ax,
        x=0.4,
        y=6.8,
        w=stage_w,
        h=stage_h,
        text="Screening",
        fc="#c9daf8",
        weight="bold",
        fontsize=9,
    )
    draw_box(
        ax,
        x=0.4,
        y=3.0,
        w=stage_w,
        h=stage_h / 2,
        text="Included",
        fc="#c9daf8",
        weight="bold",
        fontsize=9,
    )

    fig.tight_layout()
    output_path = Path(output_path)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved PRISMA diagram to {output_path}")


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 2:
        print("Usage: python prisma_from_yaml.py prisma.yaml prisma_chart.png")
        sys.exit(1)

    yaml_path, out_path = argv
    plot_prisma(yaml_path, out_path)


if __name__ == "__main__":
    main()
    # Note: supports svg. clickable links may be added in a postprocessing step
