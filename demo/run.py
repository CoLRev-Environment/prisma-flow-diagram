from py_prisma import plot_prisma2020
from py_prisma import plot_prisma_from_records

if __name__ == "__main__":

    # ============================================================
    # NEW SYSTEMATIC REVIEW
    # ============================================================

    # ------------------------------------------------------------
    # PRISMA 2020 — New systematic review (databases + registers only) (v1)
    # Template: "Identification of studies via databases and registers"
    # ------------------------------------------------------------
    plot_prisma2020(
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
        filename="prisma_new_db_registers.png",
    )

    # ------------------------------------------------------------
    # PRISMA 2020 — New systematic review (db + registers + other sources) (v2)
    # Includes "other methods" lane.
    # ------------------------------------------------------------
    plot_prisma2020(
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
                "sources": {
                    "Websites": 22,
                    "Organisations": 15,
                    "Citation searching": 41,
                }
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
        filename="prisma_new_db_registers_other.png",
    )

    # # ------------------------------------------------------------
    # # Optional: New review "databases only" (registers omitted or 0)
    # # ------------------------------------------------------------
    plot_prisma2020(
        db_registers={
            "identification": {"databases": 120, "registers": 0},
            "removed_before_screening": {"duplicates": 30, "automation": 0, "other": 0},
            "records": {"screened": 98, "excluded": 60},
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
        filename="prisma_databases_only.png",
    )

    # # ============================================================
    # # UPDATED SYSTEMATIC REVIEW
    # # (updated mode is triggered by providing "previous")
    # # ============================================================

    # # ------------------------------------------------------------
    # # PRISMA 2020 — Updated systematic review (databases + registers only) (v1)
    # #
    # # Key rule: new_db_registers must NOT have "included".
    # # New included is passed separately as new_included={...}.
    # # ------------------------------------------------------------
    plot_prisma2020(
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
        filename="prisma_updated_db_registers.png",
    )

    # # ------------------------------------------------------------
    # # PRISMA 2020 — Updated systematic review (db + registers + other sources) (v2)
    # # Two NEW-only lanes + new_included (combined across lanes).
    # # ------------------------------------------------------------
    plot_prisma2020(
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
                "sources": {
                    "Websites": 10,
                    "Organisations": 8,
                    "Citation searching": 27,
                }
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
        filename="prisma_updated_db_registers_other.png",
    )

    # TODO: try previous=.. with included=... or
    # not previous with new_included=... (test whether it throws errors)


    plot_prisma_from_records(
        # records_path="/home/gerit/ownCloud/action-office/LRDM/py-prisma/demo/data/records.bib",
        # output_path="export_test.png"
    )