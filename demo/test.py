from prisma_flow_diagram import plot_prisma2020_new

plot_prisma2020_new(
    db_registers={
        "identification": {
            "databases": {"Web of Science": 20, "Pubmed": 43},
            "registers": 10,
        },
        "removed_before_screening": {"duplicates": 30, "automation": 5},
        "records": {"screened": 95, "excluded": 55},
        "reports": {
            "sought": 40,
            "not_retrieved": 4,
            "assessed": 36,
            "excluded_reasons": {
                "Wrong population": 12,
                "Wrong outcome": 8,
            },
        },
    },
    included={"studies": 10, "reports": 12},
    filename="test.png",
)
