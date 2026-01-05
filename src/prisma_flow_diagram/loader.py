from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

import colrev.loader.load_utils

# -------------------------
# Public PRISMA 2020 interfaces
# -------------------------


@dataclass(frozen=True)
class Prisma2020New:
    db_registers: Optional[Mapping[str, Any]] = None
    included: Optional[Mapping[str, Any]] = None
    other_methods: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class Prisma2020Updated:
    previous: Mapping[str, Any]
    new_db_registers: Optional[Mapping[str, Any]] = None
    new_included: Optional[Mapping[str, Any]] = None
    other_methods: Optional[Mapping[str, Any]] = None


# -------------------------
# Flexible "reasons" model
# -------------------------


@dataclass(frozen=True)
class ReasonCounts:
    """Represents a total and/or a breakdown by reason."""

    total: Optional[int] = None
    by_reason: Optional[Mapping[str, int]] = None


ReasonsLike = Union[int, Mapping[str, int], Mapping[str, Any], ReasonCounts, None]


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
        # explicit schema
        if "total" in value or "by_reason" in value:
            total = _to_int(value.get("total"))
            by = value.get("by_reason") or value.get("reasons")
            by_reason = dict(by) if isinstance(by, Mapping) else None
            if total is None and by_reason:
                total = sum(int(v) for v in by_reason.values())
            return ReasonCounts(total=total, by_reason=by_reason)

        # treat mapping as breakdown
        by_reason = {str(k): int(v) for k, v in value.items()}
        return ReasonCounts(total=sum(by_reason.values()), by_reason=by_reason)

    return ReasonCounts(total=_to_int(value))


# -------------------------
# Internal PRISMA status
# -------------------------


@dataclass(frozen=True)
class PrismaStatus:
    databases: Optional[int] = None
    registers: Optional[int] = None

    duplicates: Optional[int] = None
    automation: Optional[int] = None
    other_removed: Optional[int] = None

    screened: Optional[int] = None
    records_excluded: Optional[int] = None  # prescreen only
    reports_sought: Optional[int] = None
    not_retrieved: Optional[int] = None
    assessed: Optional[int] = None
    reports_excluded: Optional[ReasonsLike] = None  # full-text stage

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
# Origin handling / prefix matching
# -------------------------


def _split_origin(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [p.strip() for p in value.split(";") if p.strip()]
    if isinstance(value, list):
        return [str(p).strip() for p in value if str(p).strip()]
    return []


def _has_any_origin_prefix(
    rec: Mapping[str, Any], *, origin_field: str, prefixes: list[str]
) -> bool:
    if not prefixes:
        return False
    parts = _split_origin(rec.get(origin_field))
    return any(any(p.startswith(pref) for pref in prefixes) for p in parts)


def split_records_by_origin_prefix(
    records: Dict[str, Dict[str, Any]],
    *,
    origin_field: str,
    prefixes: list[str],
    record_id_prefix_exclude: str = "md_",
) -> tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Returns (matched, rest) where `matched` are records that have at least one origin
    starting with any prefix.
    """
    matched: Dict[str, Dict[str, Any]] = {}
    rest: Dict[str, Dict[str, Any]] = {}

    for rid, rec in records.items():
        if rid.startswith(record_id_prefix_exclude):
            rest[rid] = rec
            continue

        if _has_any_origin_prefix(rec, origin_field=origin_field, prefixes=prefixes):
            matched[rid] = rec
        else:
            rest[rid] = rec

    return matched, rest


def compute_origin_stats(
    records: Dict[str, Dict[str, Any]],
    *,
    origin_field: str = "colrev_origin",
    record_id_prefix_exclude: str = "md_",
) -> tuple[Optional[int], Optional[int]]:
    """
    Returns (total_origins, duplicates_removed_estimate) where
    duplicates_removed_estimate = total_origins - kept_records.
    """
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
# Records -> PrismaStatus
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
                    fulltext_reasons[k] = fulltext_reasons.get(k, 0) + int(v)
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

    # origin-based identification is injected later (because we split by origin prefixes)
    return PrismaStatus(
        databases=None,
        registers=None,
        duplicates=None,
        automation=None,
        other_removed=None,
        screened=screened_total,
        records_excluded=buckets["prescreen_excluded"],  # prescreen only
        reports_sought=records_sought,
        not_retrieved=buckets["pdf_not_retrieved"],
        assessed=assessed,
        reports_excluded=fulltext_reasons or None,
        included=buckets["included"],
        new_reports=buckets["included"],  # keep existing behavior
    )


# -------------------------
# PrismaStatus -> PRISMA 2020 schema mappings
# -------------------------


def _prune_none(d: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _status_to_db_registers_mapping(status: PrismaStatus) -> Optional[Dict[str, Any]]:
    rc = normalize_reasons(status.reports_excluded)
    excluded_reasons: Optional[Dict[str, int]]
    if rc.by_reason:
        excluded_reasons = {str(k): int(v) for k, v in rc.by_reason.items()}
    elif rc.total is not None:
        excluded_reasons = {"Total": int(rc.total)}
    else:
        excluded_reasons = None

    db_registers: Dict[str, Any] = {}

    identification = _prune_none(
        {"databases": status.databases, "registers": status.registers}
    )
    if identification:
        db_registers["identification"] = identification

    removed_before_screening = _prune_none(
        {
            "duplicates": status.duplicates,
            "automation": status.automation,
            "other": status.other_removed,
        }
    )
    if removed_before_screening:
        db_registers["removed_before_screening"] = removed_before_screening

    records_block = _prune_none(
        {"screened": status.screened, "excluded": status.records_excluded}
    )
    if records_block:
        db_registers["records"] = records_block

    reports_block = _prune_none(
        {
            "sought": status.reports_sought,
            "not_retrieved": status.not_retrieved,
            "assessed": status.assessed,
            "excluded_reasons": excluded_reasons,
        }
    )
    if reports_block:
        db_registers["reports"] = reports_block

    return db_registers or None


def _status_to_included_mapping(status: PrismaStatus) -> Optional[Dict[str, Any]]:
    return (
        _prune_none({"studies": status.included, "reports": status.new_reports}) or None
    )


def _other_methods_mapping(count: int) -> Optional[Dict[str, Any]]:
    # Keep this minimal; adjust keys if your Prisma2020Diagram expects a different schema.
    return {"records_identified": int(count)} if count > 0 else None


# -------------------------
# Public API: load_status_from_records
# -------------------------


def load_status_from_records(
    records_path: Path | str,
    *,
    prior_reviews: list[str] | None = None,
    other_methods: list[str] | None = None,
    origin_field: str = "colrev_origin",
) -> Prisma2020New | Prisma2020Updated:
    """
    Build PRISMA inputs from CoLRev records using origin-prefix heuristics.

    - `prior_reviews`: list of prefixes (e.g., ["wagner2021.bib", "fink2023.bib"]).
      If ANY origin part starts with one of these prefixes, the record is counted as
      "study from previous review" and excluded from the new pipeline.

    - `other_methods`: list of prefixes (e.g., ["citations.bib"]).
      Among the remaining (non-prior) records, if ANY origin part starts with one of
      these prefixes, it is counted toward "other methods" identification.

    - If *no prefixes are given at all* (both lists empty/None), returns Prisma2020New
      without applying any prefix-based splitting.
    """
    prior_reviews = [p for p in (prior_reviews or []) if p]
    other_methods = [p for p in (other_methods or []) if p]

    records = load_records(records_path)

    # If no prefix logic requested: behave like a plain "new review" loader
    if not prior_reviews and not other_methods:
        status_all = records_to_status(records)
        n_origins, dup_removed = compute_origin_stats(
            records, origin_field=origin_field
        )
        status_all = PrismaStatus(
            **{**asdict(status_all), "databases": n_origins, "duplicates": dup_removed}
        )
        return Prisma2020New(
            db_registers=_status_to_db_registers_mapping(status_all),
            included=_status_to_included_mapping(status_all),
            other_methods=None,
        )

    # 1) Split out "prior review" records
    prior_recs, remaining = split_records_by_origin_prefix(
        records,
        origin_field=origin_field,
        prefixes=prior_reviews,
    )

    # 2) Among remaining, split out "other methods" records
    other_method_recs, db_recs = split_records_by_origin_prefix(
        remaining,
        origin_field=origin_field,
        prefixes=other_methods,
    )

    # New pipeline counts (screening/inclusion) should include *all* non-prior records
    new_pipeline_recs: Dict[str, Dict[str, Any]] = {**db_recs, **other_method_recs}
    status_new = records_to_status(new_pipeline_recs)

    # Identification breakdown:
    # - databases/registers: derived only from db_recs origins
    # - duplicates removed: derived from all new_pipeline_recs origins
    db_origins, _ = compute_origin_stats(db_recs, origin_field=origin_field)
    _, dup_removed_new = compute_origin_stats(
        new_pipeline_recs, origin_field=origin_field
    )

    status_new = PrismaStatus(
        **{
            **asdict(status_new),
            "databases": db_origins,
            "duplicates": dup_removed_new,
        }
    )

    # If we have prior_reviews prefixes -> Updated interface
    if prior_reviews:
        prev_count = len(prior_recs)  # "study from previous review" as requested
        previous_block: Dict[str, Any] = {"studies": prev_count, "reports": prev_count}

        return Prisma2020Updated(
            previous=previous_block,
            new_db_registers=_status_to_db_registers_mapping(status_new),
            new_included=_status_to_included_mapping(status_new),
            other_methods=_other_methods_mapping(len(other_method_recs)),
        )

    # Otherwise -> New interface (but possibly with other_methods identification)
    return Prisma2020New(
        db_registers=_status_to_db_registers_mapping(status_new),
        included=_status_to_included_mapping(status_new),
        other_methods=_other_methods_mapping(len(other_method_recs)),
    )
