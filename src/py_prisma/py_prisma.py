from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

import matplotlib.pyplot as plt
import matplotlib.patches as patches

import colrev.loader.load_utils

# ---- layout "globals" (tweak these to change proportions) ----

BASE_BOX_HEIGHT = 0.25   # base height (top/bottom margin)
PER_LINE_HEIGHT = 0.22   # extra height per line of text
MIN_BOX_HEIGHT = 0.6     # minimum height, no matter how few lines

V_GAP = 0.6              # vertical gap between boxes in a column
ARROW_MARGIN = 0.03      # small offset so arrows don't touch box edges

IDENT_PHASE_MIN_HEIGHT = 1.2

# Layout: phases start inset from the far left, then col1, then col2
CANVAS_LEFT_PAD = 0.10
PHASE_LEFT_PAD = 0.10
PHASE_W = 0.10
PHASE_TO_COL1_GAP = 0.20
COL1_TO_COL2_GAP = 0.55
RIGHT_PAD = 0.15

# Reduce whitespace above/below the illustration
TOP_ROOM = 0.70
BOTTOM_ROOM = 0.10
HEADER_GAP = 0.45

# Auto-figsize calibration (inches per axis unit)
IN_PER_X = 1.65
IN_PER_Y = 1.18
FIG_MIN_W = 10.0
FIG_MIN_H = 7.0
FIG_MAX_W = 18.0
FIG_MAX_H = 12.0


# -------------------------
# Flexible "reasons" model
# -------------------------

@dataclass
class ReasonCounts:
    """Represents a total and/or a breakdown by reason."""
    total: Optional[int] = None
    by_reason: Optional[Mapping[str, int]] = None


ReasonsLike = Union[
    int,                       # e.g., 19
    Mapping[str, int],         # e.g., {"empirical": 14, "access": 5}
    Mapping[str, Any],         # e.g., {"total": 19, "by_reason": {...}}
    ReasonCounts,              # typed form
    None,
]


def _to_int(x: Any) -> Optional[int]:
    if x is None:
        return None
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, int):
        return int(x)
    try:
        return int(str(x).strip())
    except Exception:
        return None


def normalize_reasons(value: ReasonsLike) -> ReasonCounts:
    if value is None:
        return ReasonCounts(total=None, by_reason=None)

    if isinstance(value, ReasonCounts):
        total = _to_int(value.total)
        by_reason = dict(value.by_reason) if value.by_reason else None
        return ReasonCounts(total=total, by_reason=by_reason)

    if isinstance(value, int):
        return ReasonCounts(total=value, by_reason=None)

    if isinstance(value, Mapping):
        if "by_reason" in value or "total" in value:
            total = _to_int(value.get("total"))
            by = value.get("by_reason") or value.get("reasons") or value.get("breakdown")
            by_reason: Optional[Dict[str, int]] = None
            if isinstance(by, Mapping):
                by_reason = {str(k): int(v) for k, v in by.items()}
            if total is None and by_reason:
                total = sum(by_reason.values())
            return ReasonCounts(total=total, by_reason=by_reason)

        by_reason2 = {str(k): int(v) for k, v in value.items()}
        return ReasonCounts(total=sum(by_reason2.values()), by_reason=by_reason2)

    total = _to_int(value)
    return ReasonCounts(total=total, by_reason=None)


def format_reasons_for_box(rc: ReasonCounts, fallback: str) -> str:
    if rc.by_reason:
        items = sorted(rc.by_reason.items(), key=lambda x: (-x[1], x[0]))
        return "\n".join(f"{k} (n = {v})" for k, v in items)
    if rc.total is not None:
        return f"Total (n = {rc.total})"
    return fallback


# -------------------------
# PRISMA status
# -------------------------

@dataclass
class PrismaStatus:
    # Identification
    databases: Optional[int] = None
    registers: Optional[int] = None

    # Removed before screening
    duplicates: Optional[int] = None
    automation: Optional[int] = None
    other_removed: Optional[int] = None

    # Screening + eligibility
    screened: Optional[int] = None
    records_excluded: Optional[ReasonsLike] = None   # total OR breakdown (optional)
    reports_sought: Optional[int] = None
    not_retrieved: Optional[int] = None
    assessed: Optional[int] = None
    reports_excluded: Optional[ReasonsLike] = None   # total OR breakdown

    # Included
    included: Optional[int] = None
    new_reports: Optional[int] = None


StatusLike = Union[PrismaStatus, Mapping[str, Any]]


# -------------------------
# CoLRev loading + mapping
# -------------------------

def load_records(records_path: Path | str) -> Dict[str, Dict[str, Any]]:
    return colrev.loader.load_utils.load(filename=str(records_path))


def get_status(rec: Mapping[str, Any]) -> str:
    for key in ("colrev_status", "status", "screening_status"):
        val = rec.get(key)
        if val:
            return str(val).strip()
    return ""


def status_bucket(status: str) -> str:
    s = status.lower()
    if any(x in s for x in ("md_imported", "imported", "retrieved_md", "md_retrieved")):
        return "identified"
    if any(x in s for x in ("dedupe", "duplicate", "md_duplicate")):
        return "duplicate"
    if any(x in s for x in ("prescreen", "title_abstract", "screen", "screened")):
        return "screened"
    if any(x in s for x in ("excluded", "reject")):
        return "excluded"
    if any(x in s for x in ("pdf", "fulltext", "full_text", "retrieval")):
        return "fulltext"
    if any(x in s for x in ("included", "accept", "synth")):
        return "included"
    return "other"


def _split_origin(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [p.strip() for p in value.split(";") if p.strip()]
    if isinstance(value, list):
        return [str(p).strip() for p in value if str(p).strip()]
    s = str(value).strip()
    return [s] if s else []


def compute_origin_stats(
    records: Dict[str, Dict[str, Any]],
    *,
    origin_field: str = "colrev_origin",
    record_id_prefix_exclude: str = "md_",
    origin_entry_prefix_exclude: str = "md_",
) -> tuple[Optional[int], Optional[int]]:
    """
    Returns:
      (n_origin_entries, duplicates_removed)

    Rules:
      - consider only records whose record_id does NOT start with md_
      - count total origin entries = sum(len(colrev_origin split by ';')),
        excluding origin entries that start with md_
      - duplicates_removed = n_origin_entries - n_records_in_bib (same non-md_ subset)
    """
    any_origin = False
    total_origin_entries = 0
    kept_records = 0

    for rid, rec in records.items():
        if rid.startswith(record_id_prefix_exclude):
            continue

        kept_records += 1

        origin_val = rec.get(origin_field)
        if not origin_val:
            continue

        any_origin = True
        parts = _split_origin(origin_val)
        parts = [p for p in parts if not p.startswith(origin_entry_prefix_exclude)]
        total_origin_entries += len(parts)

    if not any_origin:
        return (None, None)

    duplicates_removed = max(0, total_origin_entries - kept_records)
    return (total_origin_entries, duplicates_removed)


def parse_screening_criteria(value: Any) -> Dict[str, int]:
    """
    Parse BibTeX-like field such as:
        {non-empirical=in;bias=in}
        {non-empirical:out,bias=out}
    and return counts per criterion of being OUT/EXCLUDED.

    Rules:
      - value in {"out","exclude","excluded","0","false","no","n"} => count 1
      - value in {"in","include","included","1","true","yes","y"} => count 0
      - unknown/empty values are ignored (no entry) by default

    Returns (per record; caller aggregates across records):
      {"non-empirical": 1, "bias": 0, ...}
    """
    if not value:
        return {}

    s = str(value).strip()

    # strip outer braces if present
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()

    # tolerate trailing commas
    s = s.rstrip(",").strip()
    if not s:
        return {}

    out_vals = {"out", "exclude", "excluded", "0", "false", "no", "n"}
    in_vals = {"in", "include", "included", "1", "true", "yes", "y"}

    # split into pairs; allow both ';' and ',' as separators
    raw_parts: list[str] = []
    for chunk in s.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        raw_parts.extend([p.strip() for p in chunk.split(",") if p.strip()])

    out: Dict[str, int] = {}
    for part in raw_parts:
        # accept either "key=value" or "key:value"
        if "=" in part:
            k, v = part.split("=", 1)
        elif ":" in part:
            k, v = part.split(":", 1)
        else:
            continue

        key = k.strip()
        val = v.strip().lower()
        val = val.strip("{}").strip('"').strip("'").strip()

        if not key or not val:
            continue

        if val in out_vals:
            out[key] = 1
        elif val in in_vals:
            out[key] = 0
        else:
            # unknown value -> ignore (or set to 0 if you prefer)
            continue

    return out



def records_to_status(
    records: Dict[str, Dict[str, Any]],
    *,
    # fallback single-reason key
    exclusion_reason_key: str = "exclusion_reason",
    # preferred multi-criteria key
    screening_criteria_key: str = "screening_criteria",
) -> PrismaStatus:
    buckets = {
        "identified": 0,
        "duplicate": 0,
        "screened": 0,
        "excluded": 0,
        "fulltext": 0,
        "included": 0,
        "other": 0,
    }

    # NEW: reasons from screening_criteria
    criteria_reasons_count: Dict[str, int] = {}
    # fallback: single exclusion reason field
    single_reasons_count: Dict[str, int] = {}

    for _rid, rec in records.items():
        b = status_bucket(get_status(rec))
        buckets[b] += 1

        if b != "excluded":
            continue

        # 1) preferred: screening_criteria={a=in; b=in}
        crit = rec.get(screening_criteria_key)
        parsed = parse_screening_criteria(crit)
        if parsed:
            for reason, n in parsed.items():
                criteria_reasons_count[reason] = criteria_reasons_count.get(reason, 0) + n
            continue

        # 2) fallback: a single exclusion_reason field
        reason = str(rec.get(exclusion_reason_key, "")).strip()
        if reason:
            single_reasons_count[reason] = single_reasons_count.get(reason, 0) + 1

    screened_total = buckets["screened"] + buckets["excluded"] + buckets["fulltext"] + buckets["included"]
    reports_sought = buckets["fulltext"] + buckets["included"]
    assessed = buckets["fulltext"] + buckets["included"]

    # Databases identified + duplicates removed derived from origin stats (your rule)
    n_origin_entries, duplicates_removed = compute_origin_stats(records)

    databases_identified = (
        n_origin_entries
        if n_origin_entries is not None
        else (
            buckets["identified"]
            + buckets["screened"]
            + buckets["fulltext"]
            + buckets["included"]
            + buckets["excluded"]
            + buckets["other"]
        )
    )
    duplicates_removed_final = (
        duplicates_removed
        if duplicates_removed is not None
        else buckets["duplicate"]
    )

    # Put the detailed breakdown into reports_excluded (PRISMA “reports excluded (with reasons)” box)
    reasons_breakdown = criteria_reasons_count or single_reasons_count or None

    return PrismaStatus(
        databases=databases_identified,
        registers=None,
        duplicates=duplicates_removed_final,
        automation=None,
        other_removed=None,
        screened=screened_total,
        records_excluded=buckets["excluded"],  # keep as total; you *could* also pass a dict here
        reports_sought=reports_sought,
        not_retrieved=None,
        assessed=assessed,
        reports_excluded=reasons_breakdown,
        included=buckets["included"],
        new_reports=buckets["included"],
    )


def load_status_from_records(records_path: Path | str) -> PrismaStatus:
    return records_to_status(load_records(records_path))


# -------------------------
# Rendering helpers
# -------------------------

def _compute_column_width(
    texts: Dict[str, str],
    *,
    base_width: float = 1.1,
    char_width: float = 0.04,
    comfy_chars: int = 20,
    max_width: float = 3.2,
) -> float:
    max_chars = 0
    for text in texts.values():
        for line in text.splitlines():
            max_chars = max(max_chars, len(line))
    extra_chars = max(0, max_chars - comfy_chars)
    width = base_width + extra_chars * char_width
    return min(width, max_width)


def _compute_total_height(left_text: Dict[str, str]) -> float:
    def calc_h(text: str) -> float:
        n_lines = max(1, len(text.splitlines()))
        h = BASE_BOX_HEIGHT + n_lines * PER_LINE_HEIGHT
        return max(MIN_BOX_HEIGHT, h)

    step_order = ["ident", "screened", "sought", "assessed", "included"]
    heights = [calc_h(left_text[s]) for s in step_order]
    stack = sum(heights) + V_GAP * (len(step_order) - 1)
    return stack + TOP_ROOM + BOTTOM_ROOM + 0.55


def _auto_figsize(x_span: float, y_span: float) -> tuple[float, float]:
    w = max(FIG_MIN_W, min(FIG_MAX_W, x_span * IN_PER_X))
    h = max(FIG_MIN_H, min(FIG_MAX_H, y_span * IN_PER_Y))
    return (w, h)


# -------------------------
# Plotting
# -------------------------

def plot_simple_prisma(
    status: StatusLike,
    *,
    filename: str | Path | None = None,
    show: bool = False,
) -> None:
    if isinstance(status, PrismaStatus):
        status_map: Dict[str, Any] = asdict(status)
    elif is_dataclass(status):
        status_map = asdict(status)  # type: ignore[arg-type]
    else:
        status_map = dict(status)

    def get(key: str, default: Any = None) -> Any:
        return status_map.get(key, default)

    def present(key: str) -> bool:
        return key in status_map and status_map.get(key) is not None

    def calc_box_height(text: str) -> float:
        n_lines = max(1, len(text.splitlines()))
        height = BASE_BOX_HEIGHT + n_lines * PER_LINE_HEIGHT
        return max(MIN_BOX_HEIGHT, height)

    # ---------- TEXT PER STEP (column 1 + column 2) ----------

    ident_left_lines: list[str] = ["Records identified from:"]
    if present("databases"):
        ident_left_lines.append(f"Databases (n = {int(get('databases', 0) or 0)})")
    if present("registers"):
        ident_left_lines.append(f"Registers (n = {int(get('registers', 0) or 0)})")
    left_ident_text = "\n".join(ident_left_lines)

    included_n = int(get("included", 0) or 0)
    new_reports_n = get("new_reports", None)
    if new_reports_n not in (None, 0):
        left_included_text = (
            "New studies included in review\n"
            f"(n = {included_n})\n"
            "Reports of new included studies\n"
            f"(n = {int(new_reports_n)})"
        )
    else:
        left_included_text = "Studies included in review\n" f"(n = {included_n})"

    left_text = {
        "ident": left_ident_text,
        "screened": f"Records screened\n(n = {int(get('screened', 0) or 0)})",
        "sought": f"Reports sought for retrieval\n(n = {int(get('reports_sought', 0) or 0)})",
        "assessed": f"Reports assessed for eligibility\n(n = {int(get('assessed', 0) or 0)})",
        "included": left_included_text,
    }

    ident_right_lines: list[str] = ["Records removed before screening:"]
    if present("duplicates"):
        ident_right_lines.append(f"Duplicate records (n = {int(get('duplicates', 0) or 0)})")
    if present("automation"):
        ident_right_lines.append(
            "Records marked as ineligible by automation tools "
            f"(n = {int(get('automation', 0) or 0)})"
        )
    if present("other_removed"):
        ident_right_lines.append(f"Records removed for other reasons (n = {int(get('other_removed', 0) or 0)})")
    right_ident_text = "\n".join(ident_right_lines)

    rec_excl_rc = normalize_reasons(get("records_excluded", None))
    rec_excl_total = rec_excl_rc.total if rec_excl_rc.total is not None else 0

    rep_excl_rc = normalize_reasons(get("reports_excluded", None))

    right_text = {
        "ident": right_ident_text,
        "screened": f"Records excluded\n(n = {int(rec_excl_total)})",
        "sought": f"Reports not retrieved\n(n = {int(get('not_retrieved', 0) or 0)})",
        "assessed": "Reports excluded:\n"
        + format_reasons_for_box(
            rep_excl_rc,
            "Reason1 (n = NA)\nReason2 (n = NA)\nReason3 (n = NA)",
        ),
    }

    header_text = (
        "Identification of new studies via databases and registers"
        if present("registers")
        else "Identification of studies via databases"
    )

    box_w_col1 = _compute_column_width(left_text)
    box_w_col2 = _compute_column_width(right_text)

    phase_left = CANVAS_LEFT_PAD + PHASE_LEFT_PAD
    phase_right = phase_left + PHASE_W

    col1_left = phase_right + PHASE_TO_COL1_GAP
    XL = col1_left + box_w_col1 / 2

    col2_left = col1_left + box_w_col1 + COL1_TO_COL2_GAP
    XR = col2_left + box_w_col2 / 2

    x_max = col2_left + box_w_col2 + RIGHT_PAD
    x_span = x_max - 0.0

    y_span = _compute_total_height(left_text)
    figsize = _auto_figsize(x_span=x_span, y_span=y_span)

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0.0, x_max)
    ax.set_ylim(0.0, y_span)
    ax.axis("off")

    def draw_box(
        x_center: float,
        y_center: float,
        w: float,
        h: float,
        text: str,
        facecolor: str = "white",
        edgecolor: str = "black",
        fontsize: int = 9,
        boxstyle: str = "round,pad=0.06",
        align: str = "center",
    ) -> Dict[str, float]:
        left = x_center - w / 2
        bottom = y_center - h / 2
        rect = patches.FancyBboxPatch(
            (left, bottom),
            w,
            h,
            boxstyle=boxstyle,
            linewidth=1,
            edgecolor=edgecolor,
            facecolor=facecolor,
        )
        ax.add_patch(rect)

        if align == "left":
            text_x = left + 0.08
            ha = "left"
        else:
            text_x = x_center
            ha = "center"

        ax.text(
            text_x,
            y_center,
            text,
            ha=ha,
            va="center",
            fontsize=fontsize,
            wrap=True,
        )
        return {
            "center_x": x_center,
            "center_y": y_center,
            "left": left,
            "right": left + w,
            "bottom": bottom,
            "top": bottom + h,
            "width": w,
            "height": h,
        }

    def draw_arrow(xy_from, xy_to):
        ax.annotate("", xy=xy_to, xytext=xy_from, arrowprops=dict(arrowstyle="->", linewidth=1))

    def draw_phase_label(yc: float, height: float, text: str):
        rect = patches.FancyBboxPatch(
            (phase_left, yc - height / 2),
            PHASE_W,
            height,
            boxstyle="round,pad=0.06",
            linewidth=0,
            facecolor="#cfe2ff",
        )
        ax.add_patch(rect)
        ax.text(phase_left + PHASE_W / 2, yc, text, ha="center", va="center", rotation=90, fontsize=9)

    header_left = col1_left
    header_right = x_max - RIGHT_PAD
    header_w = max(2.5, header_right - header_left)
    header_h = 0.3
    header_y = y_span - (TOP_ROOM * 0.55)
    header_center_x = header_left + header_w / 2

    draw_box(
        x_center=header_center_x,
        y_center=header_y,
        w=header_w,
        h=header_h,
        text=header_text,
        facecolor="#f4b400",
        edgecolor="#f4b400",
        fontsize=10,
        boxstyle="round,pad=0.06",
        align="center",
    )

    step_order = ["ident", "screened", "sought", "assessed", "included"]
    left_boxes: Dict[str, Dict[str, float]] = {}

    first_height = calc_box_height(left_text["ident"])
    y_center = header_y - (header_h / 2) - HEADER_GAP - first_height / 2
    prev_step = step_order[0]
    left_boxes[prev_step] = draw_box(XL, y_center, box_w_col1, first_height, left_text[prev_step], align="left")

    for step in step_order[1:]:
        prev_box = left_boxes[prev_step]
        this_height = calc_box_height(left_text[step])
        y_center = prev_box["bottom"] - V_GAP - this_height / 2

        next_top_y = y_center + this_height / 2
        draw_arrow(
            (prev_box["center_x"], prev_box["bottom"] - ARROW_MARGIN),
            (prev_box["center_x"], next_top_y + ARROW_MARGIN),
        )

        left_boxes[step] = draw_box(XL, y_center, box_w_col1, this_height, left_text[step], align="left")
        prev_step = step

    def phase_span(boxes: list[Dict[str, float]], min_height: float | None = None) -> tuple[float, float]:
        min_bottom = min(b["bottom"] for b in boxes) - 0.05
        max_top = max(b["top"] for b in boxes) + 0.05
        center_y = (min_bottom + max_top) / 2
        height = max_top - min_bottom
        if min_height is not None and height < min_height:
            height = min_height
        return center_y, height

    id_center, id_height = phase_span([left_boxes["ident"]], min_height=IDENT_PHASE_MIN_HEIGHT)
    draw_phase_label(id_center, id_height, "Identification")

    scr_center, scr_height = phase_span([left_boxes["screened"], left_boxes["sought"], left_boxes["assessed"]])
    draw_phase_label(scr_center, scr_height, "Screening")

    inc_center, inc_height = phase_span([left_boxes["included"]])
    draw_phase_label(inc_center, inc_height, "Included")

    for step, text in right_text.items():
        ref_box = left_boxes[step]
        y_center = ref_box["center_y"]
        h = calc_box_height(text)

        right_box = draw_box(XR, y_center, box_w_col2, h, text, align="left")
        draw_arrow(
            (ref_box["right"] + ARROW_MARGIN + 0.02, ref_box["center_y"]),
            (right_box["left"] - ARROW_MARGIN - 0.02, right_box["center_y"]),
        )

    if filename is not None:
        fig.savefig(str(filename), bbox_inches="tight", dpi=300)
    if show:
        plt.show()


def plot_prisma_from_records(
    records_path: Path | str = Path("data/records.bib"),
    *,
    output_path: Path | str = Path("prisma.png"),
    show: bool = False,
) -> None:
    assert Path(records_path).exists()
    status = load_status_from_records(records_path)
    plot_simple_prisma(status, filename=output_path, show=show)


if __name__ == "__main__":
    plot_prisma_from_records()
