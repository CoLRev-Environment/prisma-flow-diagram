from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Mapping
from typing_extensions import Literal, Protocol

# flake8: noqa

# -----------------------------------------------------------------------------
# Public types
# -----------------------------------------------------------------------------

Severity = Literal["warning", "error"]
ValidationMode = Literal["off", "warn", "raise"]


@dataclass(frozen=True)
class ValidationIssue:
    severity: Severity
    code: str
    message: str
    path: str | None = None


class _DiagramLike(Protocol):
    # We avoid importing Prisma2020Diagram to prevent circular imports.
    is_updated: bool
    db_registers: Optional[Mapping[str, Any]]
    included: Optional[Mapping[str, Any]]
    other_methods: Optional[Mapping[str, Any]]
    previous: Optional[Mapping[str, Any]]
    new_db_registers: Optional[Mapping[str, Any]]
    new_included: Optional[Mapping[str, Any]]


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _as_int_maybe(x: Any) -> Optional[int]:
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


def _sum_counts_any(x: Any) -> Optional[int]:
    """
    Sum count-like values.

    Supports:
      - int/bool/str-int
      - Mapping[str, int] (breakdown) -> sum(values)
    """
    if x is None:
        return None
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, int):
        return int(x)
    if isinstance(x, Mapping):
        total = 0
        any_numeric = False
        for v in x.values():
            try:
                total += int(v)
                any_numeric = True
            except Exception:
                continue
        return total if any_numeric else 0
    try:
        return int(str(x).strip())
    except Exception:
        return None


def _get_path(d: Any, *keys: str) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, Mapping) or k not in cur:
            return None
        cur = cur[k]
    return cur


def _lane(diagram: _DiagramLike) -> Optional[Mapping[str, Any]]:
    return diagram.new_db_registers if diagram.is_updated else diagram.db_registers


def _mk(
    severity: Severity, code: str, message: str, path: str | None = None
) -> ValidationIssue:
    return ValidationIssue(severity=severity, code=code, message=message, path=path)


def _neg(x: Optional[int]) -> bool:
    return x is not None and x < 0


# -----------------------------------------------------------------------------
# Human-friendly formatting (with light color coding)
# -----------------------------------------------------------------------------

_RESET = "\x1b[0m"
_BOLD = "\x1b[1m"
_DIM = "\x1b[2m"
_RED = "\x1b[31m"
_YELLOW = "\x1b[33m"
_CYAN = "\x1b[36m"


def _color_for(severity: Severity) -> str:
    return _RED if severity == "error" else _YELLOW


def _lane_name_from_path(path: str | None) -> str:
    if not path:
        return "this lane"
    head = path.split(".", 1)[0]
    if head == "db_registers":
        return "the databases/registers lane"
    if head == "new_db_registers":
        return "the new databases/registers lane"
    if head == "other_methods":
        return "the other-methods lane"
    if head in {"included", "new_included"}:
        return "the included block"
    return head.replace("_", " ")


def _human_issue(issue: ValidationIssue) -> tuple[str, str]:
    """
    Return (title_line, body_text) where:
      - title_line is: "WARNING: Included exceeds assessed" (colored)
      - body_text contains summary + fix + rule (no bullets, no 'Where:' line)
    """
    lane_name = _lane_name_from_path(issue.path)
    msg = issue.message

    sev_word = "ERROR" if issue.severity == "error" else "WARNING"
    sev_col = _color_for(issue.severity)
    title_prefix = f"{sev_col}{sev_word}{_RESET}: "

    def body(summary: str, fix: str, rule: str) -> str:
        return "\n".join(
            [
                summary,
                f"{_CYAN}Fix:{_RESET} {fix}",
                f"{_DIM}Rule:{_RESET} {rule}",
            ]
        )

    # --- Core mappings ---
    if issue.code == "negative.count":
        title = f"{title_prefix}Negative count"
        return (
            title,
            body(
                f"A value in {lane_name} is negative. {msg}",
                "Use 0 if the step did not occur, or correct the count to be non-negative.",
                "All numeric count fields must be ≥ 0 (e.g., db_registers.records.screened, new_db_registers.reports.assessed).",
            ),
        )

    if issue.code == "inconsistent.removed_gt_identified":
        title = f"{title_prefix}Removed exceeds identified"
        return (
            title,
            body(
                f"In {lane_name}, you removed more records before screening than you identified. {msg}",
                "Reduce duplicates/automation/other removals, or increase the identified totals (databases/registers).",
                (
                    "(db_registers.removed_before_screening.duplicates + "
                    "db_registers.removed_before_screening.automation + "
                    "db_registers.removed_before_screening.other) "
                    "≤ (db_registers.identification.databases + db_registers.identification.registers)"
                ),
            ),
        )

    if issue.code == "missing.records.screened":
        title = f"{title_prefix}Missing screened count"
        return (
            title,
            body(
                f"In {lane_name}, the number of screened records is missing, so the flow may look incomplete.",
                "Provide records.screened (or set it to 0 explicitly if intentional).",
                "records.screened should be present (e.g., db_registers.records.screened; other_methods.records.screened).",
            ),
        )

    if issue.code == "suspicious.screened_gt_remaining":
        title = f"{title_prefix}Screened more than available"
        return (
            title,
            body(
                f"In {lane_name}, you screened more records than were available after removals. {msg}",
                "Reduce records.screened, or correct identification/removal counts so that the available pool is large enough.",
                (
                    "db_registers.records.screened "
                    "≤ (db_registers.identification.databases + db_registers.identification.registers "
                    "− (db_registers.removed_before_screening.duplicates + "
                    "db_registers.removed_before_screening.automation + "
                    "db_registers.removed_before_screening.other))"
                ),
            ),
        )

    if issue.code == "suspicious.excluded_gt_screened":
        title = f"{title_prefix}Excluded more than screened"
        return (
            title,
            body(
                f"In {lane_name}, you excluded more records than you screened. {msg}",
                "Reduce records.excluded, or increase records.screened if the screened count is incomplete.",
                "db_registers.records.excluded ≤ db_registers.records.screened (and likewise for other_methods.* if provided).",
            ),
        )

    if issue.code == "missing.reports.sought":
        title = f"{title_prefix}Missing reports sought"
        return (
            title,
            body(
                f"In {lane_name}, reports.sought is missing, so the full-text pipeline may look incomplete.",
                "Provide reports.sought (or set it to 0 explicitly if intentional).",
                "reports.sought should be present (e.g., db_registers.reports.sought; other_methods.reports.sought).",
            ),
        )

    if issue.code == "suspicious.not_retrieved_gt_sought":
        title = f"{title_prefix}Not retrieved exceeds sought"
        return (
            title,
            body(
                f"In {lane_name}, more reports are marked as not retrieved than were sought. {msg}",
                "Reduce reports.not_retrieved or increase reports.sought.",
                "db_registers.reports.not_retrieved ≤ db_registers.reports.sought (and likewise for other_methods.* if provided).",
            ),
        )

    if issue.code == "suspicious.assessed_gt_sought":
        title = f"{title_prefix}Assessed exceeds sought"
        return (
            title,
            body(
                f"In {lane_name}, more reports are assessed than were sought. {msg}",
                "Reduce reports.assessed or increase reports.sought.",
                "db_registers.reports.assessed ≤ db_registers.reports.sought (and likewise for other_methods.* if provided).",
            ),
        )

    if issue.code == "suspicious.sought_split_mismatch":
        title = f"{title_prefix}Sought split mismatch"
        return (
            title,
            body(
                f"In {lane_name}, the sought reports don’t match assessed + not retrieved. {msg}",
                "Adjust one of: reports.sought, reports.assessed, reports.not_retrieved so they add up consistently.",
                (
                    "Typically: db_registers.reports.sought "
                    "= db_registers.reports.assessed + db_registers.reports.not_retrieved "
                    "(and likewise for other_methods.* if provided)."
                ),
            ),
        )

    if issue.code == "suspicious.included_reports_gt_assessed":
        title = f"{title_prefix}Included exceeds assessed"
        return (
            title,
            body(
                f"In {lane_name}, more reports are included than were assessed for eligibility. {msg}",
                "Reduce included reports or increase reports.assessed if assessed is incomplete.",
                "included.reports ≤ db_registers.reports.assessed (or new_included.reports ≤ new_db_registers.reports.assessed).",
            ),
        )

    if issue.code == "missing.identification":
        title = f"{title_prefix}Missing identification block"
        return (
            title,
            body(
                f"In {lane_name}, the identification block is missing, so identified totals cannot be checked.",
                "Add identification.databases/registers (as totals or as a breakdown).",
                "Main lane should include db_registers.identification (or new_db_registers.identification in updated reviews).",
            ),
        )

    if issue.code.startswith(
        "other_methods.missing.identification"
    ) or issue.code.startswith("other_methods.invalid.identification"):
        title = f"{title_prefix}Other-methods identification incomplete"
        return (
            title,
            body(
                f"In the other-methods lane, the identification structure is missing or invalid. {msg}",
                "Provide other_methods.identification as a mapping (e.g., identification.sources={...} or a flat breakdown).",
                "other_methods.identification must be a mapping.",
            ),
        )

    if issue.code.startswith("other_methods.missing.reports") or issue.code.startswith(
        "other_methods.invalid.reports"
    ):
        title = f"{title_prefix}Other-methods reports incomplete"
        return (
            title,
            body(
                f"In the other-methods lane, the reports structure is missing or invalid. {msg}",
                "Provide other_methods.reports as a mapping (or provide a full lane with records+reports).",
                "If provided, other_methods.reports must be a mapping.",
            ),
        )

    if issue.code == "missing.lane":
        title = f"{title_prefix}Missing main lane"
        return (
            title,
            body(
                "The databases/registers lane is missing, so the diagram cannot be validated properly.",
                "Provide db_registers (new review) or new_db_registers (updated review).",
                "A PRISMA diagram requires db_registers (new) or new_db_registers (updated).",
            ),
        )

    if issue.code.startswith("missing."):
        title = f"{title_prefix}Missing required block"
        return (
            title,
            body(
                msg,
                "Provide the required block(s) for the chosen diagram mode (new vs updated).",
                "Required blocks depend on mode and must be present to plot reliably.",
            ),
        )

    # Fallback
    title = f"{title_prefix}Validation issue"
    return (
        title,
        body(
            msg,
            "Review the referenced counts/blocks and adjust to match your pipeline.",
            "See PRISMA 2020 flow logic for expected relationships between counts.",
        ),
    )


# -----------------------------------------------------------------------------
# Lane validation (shared by main lane and other_methods lane)
# -----------------------------------------------------------------------------


def _validate_lane(
    *,
    lane: Mapping[str, Any],
    issues: list[ValidationIssue],
    prefix: str,
    check_identification: bool,
) -> None:
    """
    Validate one PRISMA lane structure.

    - prefix: used in issue paths, e.g. "db_registers" or "other_methods"
    - check_identification: True for main db/register lane; False for other_methods lane
      (because other_methods identification schema differs)
    """
    identified: Optional[int] = None

    if check_identification:
        databases_val = _get_path(lane, "identification", "databases")
        registers_val = _get_path(lane, "identification", "registers")
        db_total = _sum_counts_any(databases_val)
        reg_total = _sum_counts_any(registers_val)
        if db_total is not None or reg_total is not None:
            identified = int((db_total or 0) + (reg_total or 0))

    dup = _as_int_maybe(_get_path(lane, "removed_before_screening", "duplicates"))
    auto = _as_int_maybe(_get_path(lane, "removed_before_screening", "automation"))
    other_removed = _as_int_maybe(_get_path(lane, "removed_before_screening", "other"))
    removed_sum = sum(x for x in (dup, auto, other_removed) if x is not None)

    screened = _as_int_maybe(_get_path(lane, "records", "screened"))
    excluded_records = _as_int_maybe(_get_path(lane, "records", "excluded"))

    sought = _as_int_maybe(_get_path(lane, "reports", "sought"))
    not_retrieved = _as_int_maybe(_get_path(lane, "reports", "not_retrieved"))
    assessed = _as_int_maybe(_get_path(lane, "reports", "assessed"))

    # Negative checks (errors)
    for name, val, path in [
        ("duplicates", dup, f"{prefix}.removed_before_screening.duplicates"),
        ("automation", auto, f"{prefix}.removed_before_screening.automation"),
        ("other_removed", other_removed, f"{prefix}.removed_before_screening.other"),
        ("screened", screened, f"{prefix}.records.screened"),
        ("excluded", excluded_records, f"{prefix}.records.excluded"),
        ("sought", sought, f"{prefix}.reports.sought"),
        ("not_retrieved", not_retrieved, f"{prefix}.reports.not_retrieved"),
        ("assessed", assessed, f"{prefix}.reports.assessed"),
    ]:
        if _neg(val):
            issues.append(
                _mk(
                    "error", "negative.count", f"{name} must be >= 0 (got {val}).", path
                )
            )

    if check_identification and _neg(identified):
        issues.append(
            _mk(
                "error",
                "negative.count",
                f"identified must be >= 0 (got {identified}).",
                f"{prefix}.identification",
            )
        )

    # Hard consistency (errors)
    if check_identification and identified is not None and removed_sum > identified:
        issues.append(
            _mk(
                "error",
                "inconsistent.removed_gt_identified",
                f"Identified: {identified}. Removed before screening: {removed_sum}.",
                f"{prefix}.removed_before_screening",
            )
        )

    # Plausibility (warnings)
    if screened is None:
        issues.append(
            _mk(
                "warning",
                "missing.records.screened",
                "records.screened is missing.",
                f"{prefix}.records.screened",
            )
        )

    if check_identification and identified is not None and screened is not None:
        remaining = identified - removed_sum
        if remaining >= 0 and screened > remaining:
            issues.append(
                _mk(
                    "warning",
                    "suspicious.screened_gt_remaining",
                    f"Identified: {identified}. Removed before screening: {removed_sum}. Available to screen: {remaining}. Reported as screened: {screened}.",
                    f"{prefix}.records.screened",
                )
            )

    if (
        screened is not None
        and excluded_records is not None
        and excluded_records > screened
    ):
        issues.append(
            _mk(
                "warning",
                "suspicious.excluded_gt_screened",
                f"Screened: {screened}. Excluded: {excluded_records}.",
                f"{prefix}.records.excluded",
            )
        )

    if sought is None:
        issues.append(
            _mk(
                "warning",
                "missing.reports.sought",
                "reports.sought is missing.",
                f"{prefix}.reports.sought",
            )
        )
    else:
        if not_retrieved is not None and not_retrieved > sought:
            issues.append(
                _mk(
                    "warning",
                    "suspicious.not_retrieved_gt_sought",
                    f"Sought: {sought}. Not retrieved: {not_retrieved}.",
                    f"{prefix}.reports.not_retrieved",
                )
            )
        if assessed is not None and assessed > sought:
            issues.append(
                _mk(
                    "warning",
                    "suspicious.assessed_gt_sought",
                    f"Sought: {sought}. Assessed: {assessed}.",
                    f"{prefix}.reports.assessed",
                )
            )
        if (
            assessed is not None
            and not_retrieved is not None
            and assessed + not_retrieved != sought
        ):
            issues.append(
                _mk(
                    "warning",
                    "suspicious.sought_split_mismatch",
                    f"Sought: {sought}. Assessed: {assessed}. Not retrieved: {not_retrieved}. Assessed + Not retrieved = {assessed + not_retrieved}.",
                    f"{prefix}.reports",
                )
            )


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------


def validate_diagram(diagram: _DiagramLike) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    lane = _lane(diagram)
    if lane is None:
        issues.append(
            _mk(
                "error",
                "missing.lane",
                "Missing db/registers lane block.",
                "db_registers/new_db_registers",
            )
        )
        return issues

    # Required blocks (mode-specific)
    if diagram.is_updated:
        if diagram.previous is None:
            issues.append(
                _mk(
                    "error",
                    "missing.previous",
                    "Updated review requires previous=...",
                    "previous",
                )
            )
        if diagram.new_included is None:
            issues.append(
                _mk(
                    "error",
                    "missing.new_included",
                    "Updated review requires new_included=...",
                    "new_included",
                )
            )
        if diagram.new_db_registers is None:
            issues.append(
                _mk(
                    "error",
                    "missing.new_db_registers",
                    "Updated review requires new_db_registers=...",
                    "new_db_registers",
                )
            )
    else:
        if diagram.included is None:
            issues.append(
                _mk(
                    "error",
                    "missing.included",
                    "New review requires included=...",
                    "included",
                )
            )
        if diagram.db_registers is None:
            issues.append(
                _mk(
                    "error",
                    "missing.db_registers",
                    "New review requires db_registers=...",
                    "db_registers",
                )
            )

    # Main lane
    main_prefix = "new_db_registers" if diagram.is_updated else "db_registers"
    _validate_lane(
        lane=lane, issues=issues, prefix=main_prefix, check_identification=True
    )

    # Included plausibility
    if diagram.is_updated:
        inc_block = diagram.new_included or {}
        inc_prefix = "new_included"
    else:
        inc_block = diagram.included or {}
        inc_prefix = "included"

    included_studies = _as_int_maybe(inc_block.get("studies"))
    included_reports = _as_int_maybe(inc_block.get("reports"))

    for name, val, path in [
        ("included_studies", included_studies, f"{inc_prefix}.studies"),
        ("included_reports", included_reports, f"{inc_prefix}.reports"),
    ]:
        if _neg(val):
            issues.append(
                _mk(
                    "error", "negative.count", f"{name} must be >= 0 (got {val}).", path
                )
            )

    assessed_main = _as_int_maybe(_get_path(lane, "reports", "assessed"))
    if (
        assessed_main is not None
        and included_reports is not None
        and included_reports > assessed_main
    ):
        issues.append(
            _mk(
                "warning",
                "suspicious.included_reports_gt_assessed",
                f"Assessed: {assessed_main}. Included reports: {included_reports}.",
                f"{inc_prefix}.reports",
            )
        )

    if _get_path(lane, "identification") is None:
        issues.append(
            _mk(
                "warning",
                "missing.identification",
                "identification block is missing.",
                f"{main_prefix}.identification",
            )
        )

    # other_methods
    if diagram.other_methods is not None:
        om = diagram.other_methods

        has_lane_bits = isinstance(_get_path(om, "records"), Mapping) or isinstance(
            _get_path(om, "reports"), Mapping
        )
        if has_lane_bits:
            _validate_lane(
                lane=om,
                issues=issues,
                prefix="other_methods",
                check_identification=False,
            )

        ident = _get_path(om, "identification")
        if ident is None:
            issues.append(
                _mk(
                    "warning",
                    "other_methods.missing.identification",
                    "other_methods.identification is missing.",
                    "other_methods.identification",
                )
            )
        elif not isinstance(ident, Mapping):
            issues.append(
                _mk(
                    "warning",
                    "other_methods.invalid.identification",
                    "other_methods.identification is not a mapping.",
                    "other_methods.identification",
                )
            )

        rep = _get_path(om, "reports")
        if rep is None:
            issues.append(
                _mk(
                    "warning",
                    "other_methods.missing.reports",
                    "other_methods.reports is missing.",
                    "other_methods.reports",
                )
            )
        elif not isinstance(rep, Mapping):
            issues.append(
                _mk(
                    "warning",
                    "other_methods.invalid.reports",
                    "other_methods.reports is not a mapping.",
                    "other_methods.reports",
                )
            )

    return issues


def handle_validation(
    issues: list[ValidationIssue], *, mode: ValidationMode = "warn"
) -> None:
    if mode == "off" or not issues:
        return

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    if mode == "raise" and errors:
        msg = _format_issues(errors, title="PRISMA validation failed")
        raise ValueError(msg)

    if mode == "warn" and (errors or warnings):
        out: list[str] = []
        if errors:
            out.append(
                _format_issues(
                    errors, title="PRISMA validation errors (plotting continues)"
                )
            )
        if warnings:
            out.append(_format_issues(warnings, title="PRISMA validation warnings"))
        print("\n\n".join(out))


def _format_issues(issues: list[ValidationIssue], *, title: str) -> str:
    lines = [title + ":\n"]
    for i in issues:
        title_line, body_text = _human_issue(i)
        lines.append(title_line)
        lines.append(body_text)
        lines.append("")  # blank line between issues
    return "\n".join(lines).rstrip()
