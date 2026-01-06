
<p align="center">
<img src="https://raw.githubusercontent.com/CoLRev-Environment/prisma-flow-diagram/refs/heads/main/docs/figures/logo_small.png" width="400">
</p>

<div align="center">

[![PyPI - Version](https://img.shields.io/pypi/v/prisma-flow-diagram?color=blue)](https://pypi.org/project/prisma-flow-diagram/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/prisma-flow-diagram)](https://pypi.org/project/prisma-flow-diagram/)
[![GitHub last commit](https://img.shields.io/github/last-commit/CoLRev-Environment/prisma-flow-diagram)](https://github.com/CoLRev-Environment/prisma-flow-diagram/commits/main)
[![License](https://img.shields.io/github/license/CoLRev-Environment/prisma-flow-diagram.svg)](https://github.com/CoLRev-Environment/prisma-flow-diagram/blob/main/LICENSE)

<!--
[![DOI](https://zenodo.org/badge/363073613.svg)](https://zenodo.org/badge/latestdoi/363073613)
![Documentation Status](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/colrev/docs_deploy.yml?label=documentation)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/CoLRev-Environment/colrev/tests.yml?label=tests)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/CoLRev-Environment/colrev/main.svg)](https://results.pre-commit.ci/latest/github/CoLRev-Environment/colrev/main)
![Coverage](https://raw.githubusercontent.com/CoLRev-Environment/colrev/main/tests/coverage.svg)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/bd4e44c6cda646e4b9e494c4c4d9487b)](https://app.codacy.com/gh/CoLRev-Environment/colrev/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Downloads](https://static.pepy.tech/badge/colrev/month)](https://pepy.tech/project/colrev)
[![OpenSSF Best Practices](https://bestpractices.coreinfrastructure.org/projects/7148/badge)](https://bestpractices.coreinfrastructure.org/projects/7148)
[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/CoLRev-Environment/colrev/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/CoLRev-Environment/colrev/)
-->

# A Python Package for PRISMA Flow Diagrams

</div>

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
from prisma_flow_diagram import plot_prisma2020_new, plot_prisma2020_updated

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
        "studies": 22,
        "reports":27,
    },
    filename="updated-other-methods.png",
)
```

![Updated review with other search methods](demo/updated-other-methods.png)

## Working with CoLRev Records

```python
from prisma_flow_diagram import plot_prisma_from_records

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

TODO: document how updated reviews and other search methods are added in the CoLRev workflow.

## Validation

The package validates PRISMA 2020 flow data before (and during) plotting
to catch inconsistencies.

Validation is designed to be:

-   **Non-blocking by default**: validation can be turned off, emit
    warnings, or raise errors
-   **User-friendly**: issues are reported with clear explanations and
    suggested fixes

**Example validation message**

> **WARNING**: Included exceeds assessed  
> In the databases/registers lane, more reports are included than were assessed for eligibility.  
> *Fix*: Reduce included reports or increase reports.assessed if assessed is incomplete.  
> *Rule*: included.reports ≤ db_registers.reports.assessed

### What is checked

**Required structure**

-   Presence of required top-level blocks for **new** and **updated**
    reviews
-   Presence of the main databases/registers lane
-   Presence of included and previous blocks where required

**Count validity**

-   No negative counts anywhere
-   Included study/report counts are non-negative

**Identification and screening consistency**

-   Removed records do not exceed identified records
-   Screened records do not exceed available records
-   Excluded records do not exceed screened records

**Full-text assessment consistency**

-   Reports sought is present
-   Reports not retrieved do not exceed reports sought
-   Reports assessed do not exceed reports sought
-   Assessed + not retrieved matches sought

**Included plausibility**

-   Included reports do not exceed assessed reports

**Other-methods lane**

-   Structural validity of `other_methods` blocks
-   Plausibility of counts if records or reports are provided

## License

This project is distributed under the [MIT License](LICENSE).
If you contribute to the project, you agree to share your contribution following this licenses.
