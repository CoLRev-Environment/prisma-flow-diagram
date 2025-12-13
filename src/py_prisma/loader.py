from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

import colrev.loader.load_utils

# -------------------------
# Flexible "reasons" model
# -------------------------

@dataclass
class ReasonCounts:
    """Represents a total and/or a breakdown by reason."""
    total: Optional[int] = None
    by_reason: Optional[Mapping[str, int]] = None


ReasonsLike = Union[
    int,
    Mapping[str, int],
    Mapping[str, Any],
    ReasonCounts,
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
        return ReasonCounts()

    if isinstance(value, ReasonCounts):
        return ReasonCounts(
            total=_to_int(value.total),
            by_reason=dict(value.by_reason) if value.by_reason else None,
        )

    if isinstance(value, int):
        return ReasonCounts(total=value)

    if isinstance(value, Mapping):
        if "total" in value or "by_reason" in value:
            total = _to_int(value.get("total"))
            by = value.get("by_reason") or value.get("reasons")
            by_reason = dict(by) if isinstance(by, Mapping) else None
            if total is None and by_reason:
                total = sum(by_reason.values())
            return ReasonCounts(total=total, by_reason=by_reason)

        by_reason = {str(k): int(v) for k, v in value.items()}
        return ReasonCounts(total=sum(by_reason.values()), by_reason=by_reason)

    return ReasonCounts(total=_to_int(value))


# -------------------------
# PRISMA status
# -------------------------

@dataclass
class PrismaStatus:
    databases: Optional[int] = None
    registers: Optional[int] = None

    duplicates: Optional[int] = None
    automation: Optional[int] = None
    other_removed: Optional[int] = None

    screened: Optional[int] = None
    records_excluded: Optional[int] = None          # ← prescreen only
    reports_sought: Optional[int] = None
    not_retrieved: Optional[int] = None
    assessed: Optional[int] = None
    reports_excluded: Optional[ReasonsLike] = None  # ← full-text stage

    included: Optional[int] = None
    new_reports: Optional[int] = None


# -------------------------
# CoLRev loading
# -------------------------

def load_records(records_path: Path | str) -> Dict[str, Dict[str, Any]]:
    return colrev.loader.load_utils.load(filename=str(records_path))


def get_status(rec: Mapping[str, Any]) -> str:
    for key in ("colrev_status", "status", "screening_status"):
        val = rec.get(key)
        if val:
            return str(val).strip()
    return ""


# -------------------------
# Status buckets
# -------------------------

PDF_NOT_RETRIEVED_STATUSES = {
    "pdf_needs_manual_retrieval",
    "pdf_not_available",
}

PDF_RETRIEVED_STATUSES = {
    "pdf_imported",
    "pdf_needs_manual_preparation",
    "pdf_prepared",
}


def status_bucket(status: str) -> str:
    s = status.lower()

    if "rev_prescreen_excluded" in s:
        return "prescreen_excluded"

    if any(x in s for x in ("excluded", "reject")):
        return "fulltext_excluded"

    if any(x in s for x in ("prescreen", "screened")):
        return "screened"

    if any(x in s for x in PDF_NOT_RETRIEVED_STATUSES):
        return "pdf_not_retrieved"

    if any(x in s for x in PDF_RETRIEVED_STATUSES):
        return "pdf_retrieved"

    if any(x in s for x in ("included", "accept", "synth")):
        return "included"

    if any(x in s for x in ("duplicate", "dedupe")):
        return "duplicate"

    return "other"


# -------------------------
# Origin statistics
# -------------------------

def _split_origin(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [p.strip() for p in value.split(";") if p.strip()]
    if isinstance(value, list):
        return [str(p).strip() for p in value if str(p).strip()]
    return []


def compute_origin_stats(
    records: Dict[str, Dict[str, Any]],
    *,
    origin_field: str = "colrev_origin",
    record_id_prefix_exclude: str = "md_",
) -> tuple[Optional[int], Optional[int]]:
    total_origins = 0
    kept = 0
    any_origin = False

    for rid, rec in records.items():
        if rid.startswith(record_id_prefix_exclude):
            continue
        kept += 1
        parts = _split_origin(rec.get(origin_field))
        if parts:
            any_origin = True
            total_origins += len(parts)

    if not any_origin:
        return None, None

    return total_origins, max(0, total_origins - kept)


# -------------------------
# Screening criteria parsing
# -------------------------

def parse_screening_criteria(value: Any) -> Dict[str, int]:
    if not value:
        return {}

    s = str(value).strip().strip("{}")
    out_vals = {"out", "exclude", "excluded", "0", "false", "no"}
    in_vals = {"in", "include", "included", "1", "true", "yes"}

    result: Dict[str, int] = {}
    for part in s.replace(";", ",").split(","):
        if "=" in part:
            k, v = part.split("=", 1)
        elif ":" in part:
            k, v = part.split(":", 1)
        else:
            continue

        k, v = k.strip(), v.strip().lower()
        if v in out_vals:
            result[k] = 1
        elif v in in_vals:
            result[k] = 0

    return result


# -------------------------
# Main mapping
# -------------------------

def records_to_status(
    records: Dict[str, Dict[str, Any]],
    *,
    exclusion_reason_key: str = "exclusion_reason",
    screening_criteria_key: str = "screening_criteria",
) -> PrismaStatus:

    buckets = {
        "screened": 0,
        "prescreen_excluded": 0,
        "fulltext_excluded": 0,
        "pdf_not_retrieved": 0,
        "pdf_retrieved": 0,
        "included": 0,
        "duplicate": 0,
        "other": 0,
    }

    fulltext_reasons: Dict[str, int] = {}

    for rec in records.values():
        b = status_bucket(get_status(rec))
        buckets[b] += 1

        if b == "fulltext_excluded":
            parsed = parse_screening_criteria(rec.get(screening_criteria_key))
            if parsed:
                for k, v in parsed.items():
                    fulltext_reasons[k] = fulltext_reasons.get(k, 0) + v
            else:
                r = str(rec.get(exclusion_reason_key, "")).strip()
                if r:
                    fulltext_reasons[r] = fulltext_reasons.get(r, 0) + 1

    screened_total = (
        buckets["screened"]
        + buckets["prescreen_excluded"]
        + buckets["pdf_not_retrieved"]
        + buckets["pdf_retrieved"]
        + buckets["included"]
    )

    records_sought = screened_total - buckets["prescreen_excluded"]
    assessed = buckets["pdf_retrieved"] + buckets["included"]

    n_origin, dup_removed = compute_origin_stats(records)

    return PrismaStatus(
        databases=n_origin,
        duplicates=dup_removed,
        screened=screened_total,
        records_excluded=buckets["prescreen_excluded"],   # ✅ FIX
        reports_sought=records_sought,
        not_retrieved=buckets["pdf_not_retrieved"],
        assessed=assessed,
        reports_excluded=fulltext_reasons or None,
        included=buckets["included"],
        new_reports=buckets["included"],
    )


def load_status_from_records(records_path: Path | str) -> PrismaStatus:
    return records_to_status(load_records(records_path))
