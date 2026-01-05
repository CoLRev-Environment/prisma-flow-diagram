# prisma-flow-diagram: A Python Package for PRISMA Flow Diagrams

This packages creates PRISMA 2020--style flow diagrams using matplotlib.
You provide counts for each step of your screening process, and it generates a PRISMA 2020 flow diagrams.
The design goal is a **small, transparent interface** with sensible defaults and layout that adapts to your data.

It supports:

- **New reviews** (standard PRISMA 2020 flow chrat)
- **Updated reviews** (previous + new studies)
- **Other search methods** (optional extension)

You can either:

- pass structured counts programmatically, or
- derive counts automatically from a CoLRev `records.bib` file.

Upon generating the flow diagram, the input is validated and warnings are printed when the review is incomplete or when values are inconsistent.

> **Validation that prevents common errors.**
>
> PRISMA-Py checks your counts for internal consistency *before* drawing the diagram.
> Example checks:
>
> - screened ≤ identified − removed_before_screening
> - excluded ≤ screened
> - sought = assessed + not_retrieved
>
> By default you will get readable warnings; you can also configure validation to raise errors in CI.

Output formats: PNG (other formats coming soon).

## Installation

```bash
pip install py-prisma
```

## Public API

```python
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
) -> None:


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
) -> None:
```

Note:

- `db_registers.identification.databases` can be a total or detailed breakdown (dictionary).
- `db_registers.identification.registers` is optional.


## Quick Start

### New Review

```python
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
```

![New review](demo/new.png)

### New Review with other search methods

```python
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
```

![New review with other search methods](demo/new_other-methods.png)

### Updated review

```python
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
```

![Updated review](demo/updated.png)

### Updated review with other search methods

```python
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
```

![Updated review with other search methods](demo/updated-other-methods.png)

## Working with CoLRev Records

```python
from py_prisma import plot_prisma_from_records

plot_prisma_from_records(filename="prisma_from_records.png")
```

As part of the CoLRev workflow:

```json
{
    {
    "data": {
        "data_package_endpoints": [
            {
                "endpoint": "prisma-flow-diagram"
            }
        ]
        }
    }
}
```

## License

This project is distributed under the [MIT License](LICENSE).
If you contribute to the project, you agree to share your contribution following this licenses.
