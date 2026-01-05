from prisma_flow_diagram import plot_prisma2020_new, plot_prisma2020_updated
from prisma_flow_diagram import plot_prisma_from_records
from pathlib import Path

if __name__ == "__main__":

    # ============================================================
    # NEW SYSTEMATIC REVIEW
    # ============================================================

    # ------------------------------------------------------------
    # PRISMA 2020 — New systematic review (databases + registers only) (v1)
    # Template: "Identification of studies via databases and registers"
    # ------------------------------------------------------------
    print("\n---------------------------------------------------")
    print("new.png")
    plot_prisma2020_new(
        db_registers={
            "identification": {"databases": 1842, "registers": 73},
            "removed_before_screening": {
                "duplicates": 412,
                "automation": 35,
                "other": 10,
            },
            "records": {"screened": 1458, "excluded": 1320},
            "reports": {
                "sought": 138,
                "not_retrieved": 9,
                "assessed": 129,
                "excluded_reasons": {
                    "Wrong population": 41,
                    "Wrong outcome": 28,
                    "Not primary research": 15,
                    "Duplicate report": 7,
                },
            },
        },
        # NEW-review mode: included is part of the (single) pipeline
        included={"studies": 38, "reports": 52},
        filename="new.png",
    )

    # ------------------------------------------------------------
    # PRISMA 2020 — New systematic review (db + registers + other sources) (v2)
    # Includes "other methods" lane.
    # ------------------------------------------------------------
    print("\n---------------------------------------------------")
    print("new_other-methods.png")
    plot_prisma2020_new(
        db_registers={
            "identification": {"databases": 1842, "registers": 73},
            "removed_before_screening": {
                "duplicates": 512,
                "automation": 40,
                "other": 12,
            },
            "records": {"screened": 1351, "excluded": 1220},
            "reports": {
                "sought": 131,
                "not_retrieved": 7,
                "assessed": 124,
                "excluded_reasons": {
                    "Wrong design": 33,
                    "Wrong intervention": 29,
                    "No full text": 7,
                    "Other": 15,
                },
            },
        },
        included={"studies": 40, "reports": 56},
        other_methods={
            "identification": {
                "Websites": 22,
                "Organisations": 15,
                "Citation searching": 41,
            },
            "removed_before_screening": {"duplicates": 0, "automation": 0, "other": 0},
            "records": {"screened": 78, "excluded": 60},
            "reports": {
                "sought": 18,
                "not_retrieved": 2,
                "assessed": 16,
                "excluded_reasons": {"Not relevant": 9, "Duplicate report": 2},
            },
            "included": {"studies": 5, "reports": 6},
        },
        filename="new_other-methods.png",
    )

    # ------------------------------------------------------------
    # Optional: New review "databases only" (registers omitted or 0)
    # ------------------------------------------------------------
    # TODO : registers are not really omitted...
    print("\n---------------------------------------------------")
    print("new-db-only.png")
    plot_prisma2020_new(
        db_registers={
            "identification": {"databases": 120, "registers": 0},
            "removed_before_screening": {"duplicates": 30, "automation": 0, "other": 0},
            "records": {"screened": 90, "excluded": 60},
            "reports": {
                "sought": 38,
                "not_retrieved": 4,
                "assessed": 34,
                "excluded_reasons": {
                    "No empirical data": 10,
                    "Wrong population": 8,
                    "Wrong outcome": 6,
                },
            },
        },
        included={"studies": 10},
        filename="new-db-only.png",
    )

    # ============================================================
    # UPDATED SYSTEMATIC REVIEW
    # (updated mode is triggered by providing "previous")
    # ============================================================

    # ------------------------------------------------------------
    # PRISMA 2020 — Updated systematic review (databases + registers only) (v1)
    # #
    # Key rule: new_db_registers must NOT have "included".
    # New included is passed separately as new_included={...}.
    # ------------------------------------------------------------
    print("\n---------------------------------------------------")
    print("updated.png")
    plot_prisma2020_updated(
        previous={
            "included": {"studies": 58, "reports": 74},
        },
        new_db_registers={
            "identification": {"databases": 620, "registers": 18},
            "removed_before_screening": {
                "duplicates": 101,
                "automation": 12,
                "other": 5,
            },
            "records": {"screened": 520, "excluded": 470},
            "reports": {
                "sought": 50,
                "not_retrieved": 4,
                "assessed": 46,
                "excluded_reasons": {
                    "Wrong comparator": 12,
                    "Wrong outcomes": 9,
                    "Not relevant design": 10,
                },
            },
        },
        new_included={
            "studies": 15,
            "reports": 19,
        },
        filename="updated.png",
    )

    # ------------------------------------------------------------
    # PRISMA 2020 — Updated systematic review (db + registers + other sources) (v2)
    # Two NEW-only lanes + new_included (combined across lanes).
    # ------------------------------------------------------------
    print("\n---------------------------------------------------")
    print("updated-other-methods.png")
    plot_prisma2020_updated(
        previous={
            "included": {"studies": 58, "reports": 74},
        },
        new_db_registers={
            "identification": {"databases": 620, "registers": 18},
            "removed_before_screening": {
                "duplicates": 115,
                "automation": 14,
                "other": 6,
            },
            "records": {"screened": 503, "excluded": 452},
            "reports": {
                "sought": 51,
                "not_retrieved": 3,
                "assessed": 48,
                "excluded_reasons": {
                    "Wrong intervention": 11,
                    "Wrong outcomes": 10,
                    "Not primary research": 9,
                },
            },
        },
        other_methods={
            "identification": {
                "Websites": 10,
                "Organisations": 8,
                "Citation searching": 27,
            },
            "removed_before_screening": {"duplicates": 0, "automation": 0, "other": 0},
            "records": {"screened": 45, "excluded": 35},
            "reports": {
                "sought": 10,
                "not_retrieved": 1,
                "assessed": 9,
                "excluded_reasons": {"Not relevant": 6, "Not primary research": 2},
            },
        },
        # IMPORTANT: new_included is the TOTAL newly included across all new-lanes
        new_included={
            "studies": 18 + 4,  # example: 22 new studies total
            "reports": 23 + 4,  # example: 27 new reports total
        },
        filename="updated-other-methods.png",
    )

    print("\n---------------------------------------------------")
    print("colrev_new.png")
    plot_prisma_from_records(output_path="colrev_new.png")

    print("\n---------------------------------------------------")
    print("colrev_new_other-methods.png")
    plot_prisma_from_records(
        other_methods=["Fiers2023.csv"], output_path="colrev_new_other-methods.png"
    )

    print("\n---------------------------------------------------")
    print("colrev_updated.png")
    plot_prisma_from_records(
        prior_reviews=["WagnerPresterPare2021.bib"], output_path="colrev_updated.png"
    )

    print("\n---------------------------------------------------")
    print("colrev_updated_other-methods.png")
    plot_prisma_from_records(
        prior_reviews=["WagnerPresterPare2021.bib"],
        other_methods=["Fiers2023.csv"],
        output_path="colrev_updated_other-methods.png",
    )

    # TODO: try previous=.. with included=... or
    # not previous with new_included=... (test whether it throws errors)

    print("\n\n\nValidation errors --------------------------------------")

    # ============================================================
    # EXAMPLE 1 — NEW review (intentionally broken)
    # Covers:
    #   - missing.identification
    #   - missing.records.screened
    #   - missing.reports.sought
    #   - negative.count (included.reports)
    # ============================================================
    print("\n---------------------------------------------------")
    print("bad_new_all.png")
    plot_prisma2020_new(
        db_registers={
            # identification intentionally omitted -> triggers missing.identification
            "removed_before_screening": {
                "duplicates": 5,
                "automation": 0,
                "other": 0,
            },
            "records": {
                # screened intentionally omitted -> triggers missing.records.screened
                "excluded": 10,
            },
            "reports": {
                # sought intentionally omitted -> triggers missing.reports.sought
                "not_retrieved": 2,
                "assessed": 4,
            },
        },
        included={
            "studies": 3,
            "reports": -1,  # negative -> triggers negative.count
        },
        filename="bad_new_all.png",
    )
    Path("bad_new_all.png").unlink()

    # ============================================================
    # EXAMPLE 2 — UPDATED review (intentionally broken, tries to hit most rules)
    # Covers:
    #   - inconsistent.removed_gt_identified (ERROR)
    #   - suspicious.screened_gt_remaining
    #   - suspicious.excluded_gt_screened
    #   - suspicious.not_retrieved_gt_sought
    #   - suspicious.assessed_gt_sought
    #   - suspicious.sought_split_mismatch
    #   - suspicious.included_reports_gt_assessed
    #   - other_methods.invalid.identification
    #   - other_methods.missing.reports
    # ============================================================
    print("\n---------------------------------------------------")
    print("bad_updated_all.png")
    plot_prisma2020_updated(
        previous={
            "included": {"studies": 10, "reports": 12},
        },
        new_db_registers={
            "identification": {
                "databases": {"Web of Science": 3, "PubMed": 2},  # identified = 5
                "registers": 0,
            },
            "removed_before_screening": {
                "duplicates": 6,  # removed (6) > identified (5) -> ERROR
                "automation": 0,
                "other": 0,
            },
            "records": {
                "screened": 10,  # screened > (identified - removed) => 10 > (5-6=-1) won't trigger;
                # but we still keep it to show "screened weirdness" in the printed context
                "excluded": 20,  # excluded > screened -> warning
            },
            "reports": {
                "sought": 3,
                "not_retrieved": 4,  # > sought -> warning
                "assessed": 5,  # > sought -> warning
                # assessed + not_retrieved != sought -> warning
            },
        },
        new_included={
            "studies": 2,
            "reports": 99,  # included_reports > assessed -> warning
        },
        other_methods={
            "identification": "oops-not-a-mapping",  # invalid.identification warning
            # reports intentionally omitted -> other_methods.missing.reports warning
            "records": {"screened": 1, "excluded": 0},
        },
        filename="bad_updated_all.png",
    )
    Path("bad_updated_all.png").unlink()
