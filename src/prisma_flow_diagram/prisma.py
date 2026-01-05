from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional
from typing_extensions import Literal
import matplotlib.patches as patches
import matplotlib.pyplot as plt

# NOTE:
# Validation is extracted to a separate module (recommended):
#     from .validation import validate_diagram, handle_validation
# If that import fails (e.g., single-file usage), we provide a small fallback
# validator at the bottom of this file.
from .validation import handle_validation, validate_diagram  # type: ignore

# ============================================================================
# Styling / layout configuration
# ============================================================================


@dataclass(frozen=True)
class PrismaStyle:
    # dynamic height components
    base_box_height: float = 0.25
    per_line_height: float = 0.22
    min_box_height: float = 0.6

    v_gap: float = 0.6
    arrow_margin: float = 0.03

    ident_phase_min_height: float = 1.2

    # vertical extents (top is treated as fixed; bottom can be auto-expanded for updated reviews)
    ylim: tuple[float, float] = (0.0, 9.0)

    # horizontal layout
    left_margin: float = 0.78
    right_margin: float = 0.6
    col_gap: float = 0.6  # gap between left+right columns within a lane
    lane_gap: float = 1.0  # gap between lanes

    # UPDATED reviews: extra "previous studies" lane
    prev_lane_gap: float = 0.9
    prev_header_w: float = 2.6

    # extra bottom padding (used to ensure full inclusion for deep updated-review layouts)
    bottom_padding: float = 0.5

    # headers (orange, same level)
    header_y: float = 8.4
    header_h: float = 0.3
    header_face: str = "#f4b400"
    header_edge: str = "#f4b400"

    # phase label styling (for main lane)
    phase_x: float = 0.35
    phase_bar_w: float = 0.2
    phase_face: str = "#cfe2ff"

    # box styling
    box_face: str = "white"
    box_edge: str = "black"
    box_fontsize: int = 9
    boxstyle: str = "round,pad=0.06"

    # width heuristics
    base_width: float = 1.1
    char_width: float = 0.055
    comfy_chars: int = 18
    max_width: float = 4.2


# ============================================================================
# Constants / keys
# ============================================================================

IDENT = "ident"
SCREENED = "screened"
SOUGHT = "sought"
ASSESSED = "assessed"

MAIN_STEPS = [IDENT, SCREENED, SOUGHT, ASSESSED]
OTHER_STEPS = [IDENT, SOUGHT, ASSESSED]


# ============================================================================
# Rendering primitives
# ============================================================================


@dataclass
class BoxGeometry:
    center_x: float
    center_y: float
    left: float
    right: float
    bottom: float
    top: float
    width: float
    height: float


@dataclass
class Box:
    key: str
    text: str
    x_center: float
    y_center: float
    width: float
    height: float
    align: str = "left"  # "left" or "center"

    def geometry(self) -> BoxGeometry:
        left = self.x_center - self.width / 2
        bottom = self.y_center - self.height / 2
        return BoxGeometry(
            center_x=self.x_center,
            center_y=self.y_center,
            left=left,
            right=left + self.width,
            bottom=bottom,
            top=bottom + self.height,
            width=self.width,
            height=self.height,
        )


class MatplotlibRenderer:
    def __init__(
        self,
        *,
        figsize: tuple[float, float],
        style: PrismaStyle,
        xlim: tuple[float, float],
    ):
        self.style = style
        self.fig, self.ax = plt.subplots(figsize=figsize)

        # Dynamic width: scale with x-range
        x_span = max(1.0, xlim[1] - xlim[0])
        base_span = 7.2
        width_scale = x_span / base_span
        self.fig.set_size_inches(figsize[0] * width_scale, figsize[1], forward=True)

        self.ax.set_xlim(*xlim)
        self.ax.set_ylim(*style.ylim)
        self.ax.axis("off")

    def draw_box(
        self,
        box: Box,
        *,
        facecolor: Optional[str] = None,
        edgecolor: Optional[str] = None,
        fontsize: Optional[int] = None,
        boxstyle: Optional[str] = None,
    ) -> BoxGeometry:
        g = box.geometry()
        rect = patches.FancyBboxPatch(
            (g.left, g.bottom),
            g.width,
            g.height,
            boxstyle=boxstyle or self.style.boxstyle,
            linewidth=1,
            edgecolor=edgecolor or self.style.box_edge,
            facecolor=facecolor or self.style.box_face,
        )
        self.ax.add_patch(rect)

        if box.align == "left":
            text_x = g.left + 0.08
            ha = "left"
        else:
            text_x = g.center_x
            ha = "center"

        self.ax.text(
            text_x,
            g.center_y,
            box.text,
            ha=ha,
            va="center",
            fontsize=fontsize or self.style.box_fontsize,
            wrap=True,
        )
        return g

    def draw_arrow(
        self, xy_from: tuple[float, float], xy_to: tuple[float, float]
    ) -> None:
        self.ax.annotate(
            "",
            xy=xy_to,
            xytext=xy_from,
            arrowprops=dict(arrowstyle="->", linewidth=1),
        )

    def draw_polyline_arrow(self, points: list[tuple[float, float]]) -> None:
        """Orthogonal connector with arrow head at the end."""
        if len(points) < 2:
            return
        for a, b in zip(points[:-2], points[1:-1]):
            self.ax.plot([a[0], b[0]], [a[1], b[1]], linewidth=1, color="black")
        self.ax.annotate(
            "",
            xy=points[-1],
            xytext=points[-2],
            arrowprops=dict(arrowstyle="->", linewidth=1),
        )

    def draw_phase_label(self, xc: float, yc: float, height: float, text: str) -> None:
        rect = patches.FancyBboxPatch(
            (xc - self.style.phase_bar_w / 2, yc - height / 2),
            self.style.phase_bar_w,
            height,
            boxstyle="round,pad=0.06",
            linewidth=0,
            facecolor=self.style.phase_face,
        )
        self.ax.add_patch(rect)
        self.ax.text(xc, yc, text, ha="center", va="center", rotation=90, fontsize=9)


# ============================================================================
# Layout + text models (lightweight)
# ============================================================================

PrismaSection = Mapping[str, Any]


@dataclass(frozen=True)
class TextBlocks:
    main_left: dict[str, str]
    main_right: dict[str, str]
    other_left: dict[str, str] | None
    other_right: dict[str, str] | None
    included_new: str | None
    included_updated: tuple[str, str, str] | None  # (prev, new, total)


@dataclass(frozen=True)
class Widths:
    w_main_left: float
    w_main_right: float
    w_other_left: float
    w_other_right: float
    w_included: float


@dataclass(frozen=True)
class Layout:
    # overall extent
    xlim: tuple[float, float]

    # main lane
    x_main_left: float
    x_main_right: float
    main_lane_w: float

    # other lane (optional)
    x_other_left: float | None
    x_other_right: float | None
    other_lane_w: float | None

    # previous lane (updated review only)
    x_prev_center: float | None
    prev_lane_w: float | None


@dataclass(frozen=True)
class LaneGeometries:
    main: dict[str, BoxGeometry]
    other: dict[str, BoxGeometry] | None


@dataclass(frozen=True)
class IncludedGeometries:
    # new review
    included: BoxGeometry | None

    # updated review
    prev: BoxGeometry | None
    new: BoxGeometry | None
    total: BoxGeometry | None


# ============================================================================
# Diagram builder
# ============================================================================


ValidationMode = Literal["off", "warn", "raise"]


class Prisma2020Diagram:
    def __init__(
        self,
        *,
        # NEW review inputs
        db_registers: Optional[PrismaSection] = None,
        included: Optional[PrismaSection] = None,
        other_methods: Optional[PrismaSection] = None,
        # UPDATED review inputs
        previous: Optional[PrismaSection] = None,
        new_db_registers: Optional[PrismaSection] = None,
        new_included: Optional[PrismaSection] = None,
        style: Optional[PrismaStyle] = None,
    ):
        self.style = style or PrismaStyle()

        # # NEW
        # self.db_registers = dict(db_registers) if db_registers is not None else None
        # self.included = dict(included) if included is not None else None
        # self.other_methods = dict(other_methods) if other_methods is not None else None

        # # UPDATED
        # self.previous = dict(previous) if previous is not None else None
        # self.new_db_registers = (
        #     dict(new_db_registers) if new_db_registers is not None else None
        # )
        # self.new_included = dict(new_included) if new_included is not None else None

        self.db_registers: Optional[Mapping[str, Any]] = (
            dict(db_registers) if db_registers is not None else None
        )
        self.included: Optional[Mapping[str, Any]] = (
            dict(included) if included is not None else None
        )
        self.other_methods: Optional[Mapping[str, Any]] = (
            dict(other_methods) if other_methods is not None else None
        )

        self.previous: Optional[Mapping[str, Any]] = (
            dict(previous) if previous is not None else None
        )
        self.new_db_registers: Optional[Mapping[str, Any]] = (
            dict(new_db_registers) if new_db_registers is not None else None
        )
        self.new_included: Optional[Mapping[str, Any]] = (
            dict(new_included) if new_included is not None else None
        )

        self.is_updated = (
            self.previous is not None
            or self.new_db_registers is not None
            or self.new_included is not None
        )

        if self.is_updated:
            if self.new_db_registers is None:
                raise ValueError("updated-review mode requires new_db_registers=...")
            if self.previous is None:
                raise ValueError("updated-review mode requires previous=...")
            if self.new_included is None:
                raise ValueError("updated-review mode requires new_included=...")
        else:
            if self.db_registers is None:
                raise ValueError("new-review mode requires db_registers=...")
            if self.included is None:
                raise ValueError("new-review mode requires included=...")

    def validate(self) -> list[Any]:
        """
        Returns a list of validation issues (structure defined by validation module).
        Kept intentionally untyped here to avoid importing validation types.
        """
        return validate_diagram(self)

    # ------------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------------

    @staticmethod
    def _get(d: Mapping[str, Any], key: str, default: Any = 0) -> Any:
        return d.get(key, default)

    @staticmethod
    def _has(d: Mapping[str, Any], key: str) -> bool:
        return key in d

    @staticmethod
    def _format_excluded_reasons(value: Any, fallback: str) -> str:
        if not value:
            return fallback
        if isinstance(value, Mapping):
            # stable ordering is nicer for tests and reproducible output
            items = sorted(value.items(), key=lambda kv: str(kv[0]))
            return "\n".join(f"{k} (n = {v})" for k, v in items)
        return str(value)

    @staticmethod
    def _sum_counts(value: Any) -> Optional[int]:
        """
        Support both "old" and "new" schemas:

        - old: databases: int
        - new: databases: {"Web of Science": 20, "Pubmed": 43}
        """
        if value is None:
            return None
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return int(value)
        if isinstance(value, Mapping):
            total = 0
            any_numeric = False
            for v in value.values():
                try:
                    total += int(v)
                    any_numeric = True
                except Exception:
                    continue
            return total if any_numeric else 0
        try:
            return int(str(value).strip())
        except Exception:
            return None

    @staticmethod
    def _format_breakdown(value: Any, *, indent: str = "  ") -> list[str]:
        """Format a mapping breakdown as indented lines (stable order)."""
        if not isinstance(value, Mapping) or not value:
            return []
        lines: list[str] = []
        for k, v in sorted(value.items(), key=lambda kv: str(kv[0])):
            try:
                n = int(v)
            except Exception:
                continue
            lines.append(f"{indent}{k} (n = {n})")
        return lines

    def calc_box_height(self, text: str) -> float:
        n_lines = max(1, len(text.splitlines()))
        h = self.style.base_box_height + n_lines * self.style.per_line_height
        return max(self.style.min_box_height, h)

    def compute_column_width(self, texts: Mapping[str, str]) -> float:
        style = self.style
        max_chars = 0
        for text in texts.values():
            for line in text.splitlines():
                max_chars = max(max_chars, len(line))
        if max_chars <= 0:
            return style.base_width
        extra = max(0, max_chars - style.comfy_chars)
        return min(style.base_width + extra * style.char_width, style.max_width)

    @staticmethod
    def phase_span(
        box_geoms: list[BoxGeometry], *, min_height: float | None = None
    ) -> tuple[float, float]:
        min_bottom = min(g.bottom for g in box_geoms) - 0.05
        max_top = max(g.top for g in box_geoms) + 0.05
        center_y = (min_bottom + max_top) / 2
        height = max_top - min_bottom
        if min_height is not None and height < min_height:
            height = min_height
        return center_y, height

    # ------------------------------------------------------------------------
    # Text building
    # ------------------------------------------------------------------------

    def _main_left_text(self, lane: Mapping[str, Any]) -> dict[str, str]:
        ident = dict(lane.get("identification", {}))
        records = dict(lane.get("records", {}))
        reports = dict(lane.get("reports", {}))

        ident_lines: list[str] = ["Records identified from:"]

        # --- databases: int OR mapping breakdown ---
        if self._has(ident, "databases"):
            db_val = ident.get("databases")
            db_total = self._sum_counts(db_val) or 0
            ident_lines.append(f"Databases (n = {db_total})")
            ident_lines.extend(self._format_breakdown(db_val))

        # --- registers: int OR mapping breakdown (supported for completeness) ---
        if self._has(ident, "registers"):
            reg_val = ident.get("registers")
            reg_total = self._sum_counts(reg_val) or 0
            ident_lines.append(f"Registers (n = {reg_total})")
            ident_lines.extend(self._format_breakdown(reg_val))

        return {
            IDENT: "\n".join(ident_lines),
            SCREENED: f"Records screened\n(n = {self._get(records, 'screened', 0)})",
            SOUGHT: f"Reports sought for retrieval\n(n = {self._get(reports, 'sought', 0)})",
            ASSESSED: f"Reports assessed for eligibility\n(n = {self._get(reports, 'assessed', 0)})",
        }

    def _main_right_text(self, lane: Mapping[str, Any]) -> dict[str, str]:
        removed = dict(lane.get("removed_before_screening", {}))
        records = dict(lane.get("records", {}))
        reports = dict(lane.get("reports", {}))

        ident_lines: list[str] = ["Records removed before screening:"]
        if self._has(removed, "duplicates"):
            ident_lines.append(
                f"Duplicate records (n = {self._get(removed, 'duplicates', 0)})"
            )
        if self._has(removed, "automation"):
            ident_lines.append(
                "Records marked as ineligible by automation tools "
                f"(n = {self._get(removed, 'automation', 0)})"
            )
        if self._has(removed, "other"):
            ident_lines.append(
                f"Records removed for other reasons (n = {self._get(removed, 'other', 0)})"
            )

        excluded_reasons = self._get(reports, "excluded_reasons", None)
        return {
            IDENT: "\n".join(ident_lines),
            SCREENED: f"Records excluded\n(n = {self._get(records, 'excluded', 0)})",
            SOUGHT: f"Reports not retrieved\n(n = {self._get(reports, 'not_retrieved', 0)})",
            ASSESSED: "Reports excluded:\n"
            + self._format_excluded_reasons(
                excluded_reasons,
                "Reason1 (n = NA)\nReason2 (n = NA)\nReason3 (n = NA)",
            ),
        }

    def _other_left_text(self) -> dict[str, str]:
        assert self.other_methods is not None

        ident_raw = self.other_methods.get("identification", {})
        ident = dict(ident_raw) if isinstance(ident_raw, Mapping) else {}

        # Support both:
        #   - identification: { "sources": { ... } }
        #   - identification: { "Websites": 10, "Organisations": 8, ... }
        sources_raw = ident.get("sources")
        if isinstance(sources_raw, Mapping):
            sources = sources_raw
        else:
            # treat the entire identification mapping as sources if it looks like a breakdown
            sources = ident

        reports_raw = self.other_methods.get("reports", {})
        reports = dict(reports_raw) if isinstance(reports_raw, Mapping) else {}

        ident_lines: list[str] = ["Records identified from:"]
        if isinstance(sources, Mapping) and sources:
            for name, n in sources.items():
                # be tolerant: display raw if int cast fails
                try:
                    n_int = int(n)
                    ident_lines.append(f"{name} (n = {n_int})")
                except Exception:
                    ident_lines.append(f"{name} (n = {n})")
        else:
            ident_lines.append("Websites (n = )")
            ident_lines.append("Organisations (n = )")
            ident_lines.append("Citation searching (n = )")
            ident_lines.append("etc.")

        return {
            IDENT: "\n".join(ident_lines),
            SOUGHT: f"Reports sought for retrieval\n(n = {self._get(reports, 'sought', 0)})",
            ASSESSED: f"Reports assessed for eligibility\n(n = {self._get(reports, 'assessed', 0)})",
        }

    def _other_right_text(self) -> dict[str, str]:
        assert self.other_methods is not None

        reports_raw = self.other_methods.get("reports", {})
        reports = dict(reports_raw) if isinstance(reports_raw, Mapping) else {}

        excluded_reasons = self._get(reports, "excluded_reasons", None)
        return {
            SOUGHT: f"Reports not retrieved\n(n = {self._get(reports, 'not_retrieved', 0)})",
            ASSESSED: "Reports excluded:\n"
            + self._format_excluded_reasons(
                excluded_reasons,
                "Reason1 (n = NA)\nReason2 (n = NA)\nReason3 (n = NA)",
            ),
        }

    @staticmethod
    def _fmt_included_block(
        *,
        label_studies: str,
        n_studies: int,
        label_reports: str,
        n_reports: Optional[int],
    ) -> str:
        if n_reports is None:
            return f"{label_studies}\n(n = {n_studies})"
        return f"{label_studies}\n(n = {n_studies})\n{label_reports}\n(n = {n_reports})"

    def _included_new_review_text(self) -> str:
        assert self.included is not None
        studies = int(self._get(self.included, "studies", 0))
        reports = (
            int(self._get(self.included, "reports", 0))
            if "reports" in self.included
            else None
        )
        return self._fmt_included_block(
            label_studies="Studies included in review",
            n_studies=studies,
            label_reports="Reports of included studies",
            n_reports=reports,
        )

    def _included_updated_texts(self) -> tuple[str, str, str]:
        assert self.previous is not None and self.new_included is not None

        # Expect: previous={"included": {"studies": ..., "reports": ...}}
        prev_inc = dict(self.previous.get("included", {}))
        prev_studies = int(self._get(prev_inc, "studies", 0))
        prev_reports = (
            int(self._get(prev_inc, "reports", 0)) if "reports" in prev_inc else None
        )

        new_studies = int(self._get(self.new_included, "studies", 0))
        new_reports = (
            int(self._get(self.new_included, "reports", 0))
            if "reports" in self.new_included
            else None
        )

        total_studies = prev_studies + new_studies
        if prev_reports is None and new_reports is None:
            total_reports: Optional[int] = None
        else:
            total_reports = int(prev_reports or 0) + int(new_reports or 0)

        prev_text = self._fmt_included_block(
            label_studies="Previous studies",
            n_studies=prev_studies,
            label_reports="Reports of previous studies",
            n_reports=prev_reports,
        )
        new_text = self._fmt_included_block(
            label_studies="New studies included in review",
            n_studies=new_studies,
            label_reports="Reports of new included studies",
            n_reports=new_reports,
        )
        total_text = self._fmt_included_block(
            label_studies="Total studies included in review",
            n_studies=total_studies,
            label_reports="Reports of total included studies",
            n_reports=total_reports,
        )
        return prev_text, new_text, total_text

    def _build_text_blocks(self) -> TextBlocks:
        main_lane = self.new_db_registers if self.is_updated else self.db_registers
        assert main_lane is not None

        main_left = self._main_left_text(main_lane)
        main_right = self._main_right_text(main_lane)

        other_left = other_right = None
        if self.other_methods is not None:
            other_left = self._other_left_text()
            other_right = self._other_right_text()

        if self.is_updated:
            inc_updated = self._included_updated_texts()
            inc_new = None
        else:
            inc_new = self._included_new_review_text()
            inc_updated = None

        return TextBlocks(
            main_left=main_left,
            main_right=main_right,
            other_left=other_left,
            other_right=other_right,
            included_new=inc_new,
            included_updated=inc_updated,
        )

    # ------------------------------------------------------------------------
    # Width + layout computation
    # ------------------------------------------------------------------------

    def _compute_widths(self, texts: TextBlocks) -> Widths:
        w_main_left = self.compute_column_width(texts.main_left)
        w_main_right = self.compute_column_width(texts.main_right)

        if texts.other_left is not None and texts.other_right is not None:
            w_other_left = self.compute_column_width(texts.other_left)
            w_other_right = self.compute_column_width(texts.other_right)
        else:
            w_other_left = 0.0
            w_other_right = 0.0

        if self.is_updated:
            assert texts.included_updated is not None
            prev_text, new_text, total_text = texts.included_updated
            w_included = self.compute_column_width(
                {"prev": prev_text, "new": new_text, "total": total_text}
            )
        else:
            assert texts.included_new is not None
            w_included = self.compute_column_width({"inc": texts.included_new})

        return Widths(
            w_main_left=w_main_left,
            w_main_right=w_main_right,
            w_other_left=w_other_left,
            w_other_right=w_other_right,
            w_included=w_included,
        )

    def _compute_layout(self, widths: Widths, *, has_other: bool) -> Layout:
        style = self.style
        x = style.left_margin

        x_prev_center: float | None = None
        prev_lane_w: float | None = None
        if self.is_updated:
            prev_lane_w = max(style.prev_header_w, widths.w_included)
            x_prev_center = x + prev_lane_w / 2
            x = x_prev_center + prev_lane_w / 2 + style.prev_lane_gap

        x_main_left = x + widths.w_main_left / 2
        x_main_right = (
            x_main_left
            + widths.w_main_left / 2
            + style.col_gap
            + widths.w_main_right / 2
        )
        main_lane_w = widths.w_main_left + style.col_gap + widths.w_main_right

        x = (
            x_main_right
            + widths.w_main_right / 2
            + (style.lane_gap if has_other else 0.0)
        )

        x_other_left: float | None = None
        x_other_right: float | None = None
        other_lane_w: float | None = None

        if has_other:
            x_other_left = x + widths.w_other_left / 2
            x_other_right = (
                x_other_left
                + widths.w_other_left / 2
                + style.col_gap
                + widths.w_other_right / 2
            )
            other_lane_w = widths.w_other_left + style.col_gap + widths.w_other_right
            x_end = x_other_right + widths.w_other_right / 2 + style.right_margin
        else:
            x_end = x_main_right + widths.w_main_right / 2 + style.right_margin

        return Layout(
            xlim=(0.0, x_end),
            x_main_left=x_main_left,
            x_main_right=x_main_right,
            main_lane_w=main_lane_w,
            x_other_left=x_other_left,
            x_other_right=x_other_right,
            other_lane_w=other_lane_w,
            x_prev_center=x_prev_center,
            prev_lane_w=prev_lane_w,
        )

    # ------------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------------

    def _draw_vertical_flow(
        self,
        *,
        renderer: MatplotlibRenderer,
        x_center: float,
        steps: list[str],
        texts: dict[str, str],
        box_width: float,
        start_y_center: float,
        forced_y: Optional[dict[str, float]] = None,
    ) -> dict[str, BoxGeometry]:
        style = self.style
        geoms: dict[str, BoxGeometry] = {}

        first = steps[0]
        y = forced_y[first] if forced_y and first in forced_y else start_y_center
        h0 = self.calc_box_height(texts[first])
        geoms[first] = renderer.draw_box(
            Box(first, texts[first], x_center, y, box_width, h0, align="left")
        )

        prev = first
        for step in steps[1:]:
            prev_g = geoms[prev]
            h = self.calc_box_height(texts[step])
            if forced_y and step in forced_y:
                y = forced_y[step]
            else:
                y = prev_g.bottom - style.v_gap - h / 2

            next_top_y = y + h / 2
            renderer.draw_arrow(
                (prev_g.center_x, prev_g.bottom - style.arrow_margin),
                (prev_g.center_x, next_top_y + style.arrow_margin),
            )
            geoms[step] = renderer.draw_box(
                Box(step, texts[step], x_center, y, box_width, h, align="left")
            )
            prev = step

        return geoms

    def _draw_side_box(
        self,
        *,
        renderer: MatplotlibRenderer,
        ref_left: BoxGeometry,
        text: str,
        x_center: float,
        width: float,
    ) -> BoxGeometry:
        style = self.style
        h = self.calc_box_height(text)
        g = renderer.draw_box(
            Box("side", text, x_center, ref_left.center_y, width, h, align="left")
        )
        renderer.draw_arrow(
            (ref_left.right + style.arrow_margin + 0.02, ref_left.center_y),
            (g.left - style.arrow_margin - 0.02, g.center_y),
        )
        return g

    def _draw_prev_to_total_routed(
        self,
        *,
        renderer: MatplotlibRenderer,
        prev_geom: BoxGeometry,
        total_geom: BoxGeometry,
    ) -> None:
        """Route: DOWN from previous box, then RIGHT into total box (arrow head)."""
        style = self.style
        start = (prev_geom.center_x, prev_geom.bottom - style.arrow_margin)
        elbow_y = min(prev_geom.bottom - style.v_gap, total_geom.center_y)
        end = (total_geom.left + 0.06, elbow_y)
        renderer.draw_polyline_arrow([start, (prev_geom.center_x, elbow_y), end])

    # ------------------------------------------------------------------------
    # Drawing: headers / lanes / included / labels
    # ------------------------------------------------------------------------

    def _draw_headers(
        self, renderer: MatplotlibRenderer, layout: Layout, *, has_other: bool
    ) -> None:
        style = self.style

        hdr_main_text = (
            "Identification of studies via databases, registers and other sources"
            if not self.is_updated
            else "Identification of new studies via databases, registers and other sources"
        )
        renderer.draw_box(
            Box(
                "hdr_main",
                hdr_main_text,
                (layout.x_main_left + layout.x_main_right) / 2,
                style.header_y,
                layout.main_lane_w,
                style.header_h,
                align="center",
            ),
            facecolor=style.header_face,
            edgecolor=style.header_edge,
            fontsize=10,
        )

        if self.is_updated:
            assert layout.x_prev_center is not None and layout.prev_lane_w is not None
            renderer.draw_box(
                Box(
                    "hdr_prev",
                    "Previous studies",
                    layout.x_prev_center,
                    style.header_y,
                    layout.prev_lane_w,
                    style.header_h,
                    align="center",
                ),
                facecolor=style.header_face,
                edgecolor=style.header_edge,
                fontsize=10,
            )

        if has_other:
            assert (
                layout.x_other_left is not None
                and layout.x_other_right is not None
                and layout.other_lane_w is not None
            )
            renderer.draw_box(
                Box(
                    "hdr_other",
                    "Identification of studies via other methods",
                    (layout.x_other_left + layout.x_other_right) / 2,
                    style.header_y,
                    layout.other_lane_w,
                    style.header_h,
                    align="center",
                ),
                facecolor=style.header_face,
                edgecolor=style.header_edge,
                fontsize=10,
            )

    def _draw_lanes(
        self,
        *,
        renderer: MatplotlibRenderer,
        layout: Layout,
        widths: Widths,
        texts: TextBlocks,
    ) -> LaneGeometries:
        # main lane
        main_geoms = self._draw_vertical_flow(
            renderer=renderer,
            x_center=layout.x_main_left,
            steps=MAIN_STEPS,
            texts=texts.main_left,
            box_width=widths.w_main_left,
            start_y_center=7.1,
        )
        for step in MAIN_STEPS:
            self._draw_side_box(
                renderer=renderer,
                ref_left=main_geoms[step],
                text=texts.main_right[step],
                x_center=layout.x_main_right,
                width=widths.w_main_right,
            )

        # other lane (optional), aligned to main
        other_geoms: dict[str, BoxGeometry] | None = None
        if texts.other_left is not None and texts.other_right is not None:
            assert layout.x_other_left is not None and layout.x_other_right is not None
            forced_y = {
                IDENT: main_geoms[IDENT].center_y,
                SOUGHT: main_geoms[SOUGHT].center_y,
                ASSESSED: main_geoms[ASSESSED].center_y,
            }
            other_geoms = self._draw_vertical_flow(
                renderer=renderer,
                x_center=layout.x_other_left,
                steps=OTHER_STEPS,
                texts=texts.other_left,
                box_width=widths.w_other_left,
                start_y_center=7.1,
                forced_y=forced_y,
            )
            for step in [SOUGHT, ASSESSED]:
                self._draw_side_box(
                    renderer=renderer,
                    ref_left=other_geoms[step],
                    text=texts.other_right[step],
                    x_center=layout.x_other_right,
                    width=widths.w_other_right,
                )

        return LaneGeometries(main=main_geoms, other=other_geoms)

    def _lowest_assessed_bottom(self, lane_geoms: LaneGeometries) -> float:
        lowest = lane_geoms.main[ASSESSED].bottom
        if lane_geoms.other is not None:
            lowest = min(lowest, lane_geoms.other[ASSESSED].bottom)
        return lowest

    def _connect_other_assessed_to_included(
        self,
        *,
        renderer: MatplotlibRenderer,
        other_assessed: BoxGeometry,
        target: BoxGeometry,
    ) -> None:
        style = self.style
        elbow_y = target.center_y
        renderer.draw_polyline_arrow(
            [
                (other_assessed.center_x, other_assessed.bottom - style.arrow_margin),
                (other_assessed.center_x, elbow_y),
                (target.right + style.arrow_margin, elbow_y),
                (target.right, target.center_y),
            ]
        )

    def _draw_included_new(
        self,
        *,
        renderer: MatplotlibRenderer,
        layout: Layout,
        widths: Widths,
        texts: TextBlocks,
        lanes: LaneGeometries,
    ) -> IncludedGeometries:
        style = self.style
        assert texts.included_new is not None

        inc_text = texts.included_new
        inc_h = self.calc_box_height(inc_text)

        inc_y = self._lowest_assessed_bottom(lanes) - style.v_gap - inc_h / 2
        inc_geom = renderer.draw_box(
            Box(
                "included",
                inc_text,
                layout.x_main_left,
                inc_y,
                widths.w_included,
                inc_h,
                align="left",
            )
        )

        renderer.draw_arrow(
            (
                lanes.main[ASSESSED].center_x,
                lanes.main[ASSESSED].bottom - style.arrow_margin,
            ),
            (inc_geom.center_x, inc_geom.top + style.arrow_margin),
        )

        if lanes.other is not None:
            self._connect_other_assessed_to_included(
                renderer=renderer, other_assessed=lanes.other[ASSESSED], target=inc_geom
            )

        return IncludedGeometries(included=inc_geom, prev=None, new=None, total=None)

    def _draw_included_updated(
        self,
        *,
        renderer: MatplotlibRenderer,
        layout: Layout,
        widths: Widths,
        texts: TextBlocks,
        lanes: LaneGeometries,
    ) -> IncludedGeometries:
        style = self.style
        assert texts.included_updated is not None
        assert layout.x_prev_center is not None

        prev_text, new_text, total_text = texts.included_updated

        # new included (below assessed)
        new_h = self.calc_box_height(new_text)
        new_y = self._lowest_assessed_bottom(lanes) - style.v_gap - new_h / 2
        new_geom = renderer.draw_box(
            Box(
                "new_included",
                new_text,
                layout.x_main_left,
                new_y,
                widths.w_included,
                new_h,
                align="left",
            )
        )

        # total included (below new)
        total_h = self.calc_box_height(total_text)
        total_y = new_geom.bottom - style.v_gap - total_h / 2
        total_geom = renderer.draw_box(
            Box(
                "total_included",
                total_text,
                layout.x_main_left,
                total_y,
                widths.w_included,
                total_h,
                align="left",
            )
        )

        # previous included (lane at top aligned with main identification)
        prev_h = self.calc_box_height(prev_text)
        prev_y = lanes.main[IDENT].center_y
        prev_geom = renderer.draw_box(
            Box(
                "previous",
                prev_text,
                layout.x_prev_center,
                prev_y,
                widths.w_included,
                prev_h,
                align="left",
            )
        )

        # connectors
        renderer.draw_arrow(
            (
                lanes.main[ASSESSED].center_x,
                lanes.main[ASSESSED].bottom - style.arrow_margin,
            ),
            (new_geom.center_x, new_geom.top + style.arrow_margin),
        )

        if lanes.other is not None:
            self._connect_other_assessed_to_included(
                renderer=renderer, other_assessed=lanes.other[ASSESSED], target=new_geom
            )

        renderer.draw_arrow(
            (new_geom.center_x, new_geom.bottom - style.arrow_margin),
            (total_geom.center_x, total_geom.top + style.arrow_margin),
        )

        self._draw_prev_to_total_routed(
            renderer=renderer, prev_geom=prev_geom, total_geom=total_geom
        )

        # ensure bottom is included
        desired_ymin = min(style.ylim[0], total_geom.bottom - style.bottom_padding)
        renderer.ax.set_ylim(desired_ymin, style.ylim[1])

        return IncludedGeometries(
            included=None, prev=prev_geom, new=new_geom, total=total_geom
        )

    def _draw_included(
        self,
        *,
        renderer: MatplotlibRenderer,
        layout: Layout,
        widths: Widths,
        texts: TextBlocks,
        lanes: LaneGeometries,
    ) -> IncludedGeometries:
        if self.is_updated:
            return self._draw_included_updated(
                renderer=renderer,
                layout=layout,
                widths=widths,
                texts=texts,
                lanes=lanes,
            )
        return self._draw_included_new(
            renderer=renderer, layout=layout, widths=widths, texts=texts, lanes=lanes
        )

    def _draw_phase_labels(
        self,
        *,
        renderer: MatplotlibRenderer,
        lanes: LaneGeometries,
        included: IncludedGeometries,
    ) -> None:
        style = self.style

        id_center, id_height = self.phase_span(
            [lanes.main[IDENT]], min_height=style.ident_phase_min_height
        )
        renderer.draw_phase_label(style.phase_x, id_center, id_height, "Identification")

        scr_center, scr_height = self.phase_span(
            [lanes.main[SCREENED], lanes.main[SOUGHT], lanes.main[ASSESSED]]
        )
        renderer.draw_phase_label(style.phase_x, scr_center, scr_height, "Screening")

        if included.included is not None:
            inc_center, inc_height = self.phase_span([included.included])
        else:
            assert included.new is not None and included.total is not None
            inc_center, inc_height = self.phase_span([included.new, included.total])
        renderer.draw_phase_label(style.phase_x, inc_center, inc_height, "Included")

    # ------------------------------------------------------------------------
    # Public plot
    # ------------------------------------------------------------------------

    def plot(
        self,
        *,
        filename: str | None = None,
        show: bool = False,
        figsize: tuple[float, float] = (14, 10),
        validation: ValidationMode = "warn",
    ) -> None:
        # ---- validation hook (before any drawing) ----
        if validation != "off":
            issues = self.validate()
            handle_validation(issues, mode=validation)

        texts = self._build_text_blocks()
        has_other = texts.other_left is not None and texts.other_right is not None

        widths = self._compute_widths(texts)
        layout = self._compute_layout(widths, has_other=has_other)

        renderer = MatplotlibRenderer(
            figsize=figsize, style=self.style, xlim=layout.xlim
        )

        self._draw_headers(renderer, layout, has_other=has_other)
        lanes = self._draw_lanes(
            renderer=renderer, layout=layout, widths=widths, texts=texts
        )
        included = self._draw_included(
            renderer=renderer, layout=layout, widths=widths, texts=texts, lanes=lanes
        )
        self._draw_phase_labels(renderer=renderer, lanes=lanes, included=included)

        if filename is not None:
            renderer.fig.savefig(filename, bbox_inches="tight", dpi=300)
        if show:
            plt.show()


# ============================================================================
# Public API
# ============================================================================


def plot_prisma2020_new(
    *,
    db_registers: Mapping[str, Any],
    included: Mapping[str, Any],
    other_methods: Mapping[str, Any] | None = None,
    # output
    filename: str | None = None,
    show: bool = False,
    figsize: tuple[float, float] = (14, 10),
    style: PrismaStyle | None = None,
    validation: ValidationMode = "warn",
) -> None:
    Prisma2020Diagram(
        db_registers=db_registers,
        included=included,
        other_methods=other_methods,
        previous=None,
        new_db_registers=None,
        new_included=None,
        style=style,
    ).plot(
        filename=filename,
        show=show,
        figsize=figsize,
        validation=validation,
    )


def plot_prisma2020_updated(
    *,
    previous: Mapping[str, Any],
    new_db_registers: Mapping[str, Any],
    new_included: Mapping[str, Any],
    other_methods: Mapping[str, Any] | None = None,
    # output
    filename: str | None = None,
    show: bool = False,
    figsize: tuple[float, float] = (14, 10),
    style: PrismaStyle | None = None,
    validation: ValidationMode = "warn",
) -> None:
    Prisma2020Diagram(
        db_registers=None,
        included=None,
        other_methods=other_methods,
        previous=previous,
        new_db_registers=new_db_registers,
        new_included=new_included,
        style=style,
    ).plot(
        filename=filename,
        show=show,
        figsize=figsize,
        validation=validation,
    )


# ============================================================================
# Fallback validation (only used if .validation module isn't available)
# ============================================================================


@dataclass(frozen=True)
class ValidationIssue:
    severity: Literal["warning", "error"]
    code: str
    message: str
    path: str | None = None
