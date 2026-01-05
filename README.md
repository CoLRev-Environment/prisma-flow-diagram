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
from py_prisma import plot_prisma2020_new

plot_prisma2020_new(
    db_registers={
        "identification": {"databases": {"Web of Science": 20, "Pubmed": 43}, "registers": 10},
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
