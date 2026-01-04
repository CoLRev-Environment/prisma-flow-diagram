# PRISMA-Py: A Python Package for PRISMA 2020 Flow Charts

This packages creates PRISMA 2020--style flow diagrams using matplotlib.
You provide counts for each step of your screening process, and it generates a PRISMA 2020 flow chart.

It supports:

- **New reviews** (standard PRISMA 2020 flow chrat)
- **Updated reviews** (previous + new studies)
- **Other search methods** (optional extension)

You can either:

- pass structured counts programmatically, or
- **derive counts automatically from a CoLRev `records.bib` file**.

The design goal is a **small, transparent interface** with sensible defaults and layout that adapts to your data.

Output formats: PNG (other formats coming soon).

## Installation

```bash
pip install py-prisma
```

## Quick Start

### New Review

```python
from py_prisma import plot_prisma2020

plot_prisma2020(
    db_registers={
        "identification": {"databases": 120, "registers": 10},
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
    filename="prisma.png",
)
```

### Updated review

TODO

### Other search methods

TODO

## Working with CoLRev Records

```python
from py_prisma import plot_prisma_from_records

plot_prisma_from_records(filename="prisma_from_records.png")
```

## License

This project is distributed under the [MIT License](LICENSE).
If you contribute to the project, you agree to share your contribution following this licenses.
