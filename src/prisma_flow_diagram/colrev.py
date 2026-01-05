#! /usr/bin/env python
"""Creation of a PRISMA chart as part of the data operations"""
from __future__ import annotations

import logging
import typing
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field

import colrev.env.docker_manager
import colrev.env.utils
import colrev.package_manager.package_base_classes as base_classes
import colrev.package_manager.package_settings
from prisma_flow_diagram import plot_prisma_from_records

if typing.TYPE_CHECKING:
    import colrev.ops.data


class PRISMA(base_classes.DataPackageBaseClass):
    """Create a PRISMA diagram"""

    ci_supported: bool = Field(default=False)

    class PRISMASettings(
        colrev.package_manager.package_settings.DefaultSettings, BaseModel
    ):
        """PRISMA settings"""

        endpoint: str
        version: str
        diagram_path: typing.List[Path] = Field(
            default_factory=lambda: [Path("PRISMA.png")]
        )

    settings_class = PRISMASettings

    def __init__(
        self,
        *,
        data_operation: colrev.ops.data.Data,  # pylint: disable=unused-argument
        settings: dict,
        logger: typing.Optional[logging.Logger] = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.review_manager = data_operation.review_manager
        self.data_operation = data_operation

        # Set default values (if necessary)
        if "version" not in settings:
            settings["version"] = "0.1"

        if "diagram_path" in settings:
            settings["diagram_path"] = [Path(path) for path in settings["diagram_path"]]
        else:
            settings["diagram_path"] = [Path("PRISMA.png")]

        self.settings = self.settings_class(**settings)

        output_dir = self.review_manager.paths.output
        self.csv_path = output_dir / Path("PRISMA.csv")

        self.settings.diagram_path = [
            output_dir / path for path in self.settings.diagram_path
        ]

    # pylint: disable=unused-argument
    @classmethod
    def add_endpoint(cls, operation: colrev.ops.data.Data, params: str) -> None:
        """Add as an endpoint"""

        add_package = {
            "endpoint": "colrev.prisma",
            "version": "0.1",
            "diagram_path": ["PRISMA.png"],
        }
        operation.review_manager.settings.data.data_package_endpoints.append(
            add_package
        )

    def update_data(
        self,
        records: dict,  # pylint: disable=unused-argument
        synthesized_record_status_matrix: dict,  # pylint: disable=unused-argument
        silent_mode: bool,
    ) -> None:
        """Update the data/prisma diagram"""

        plot_prisma_from_records(output_path="colrev_new.png")

    def update_record_status_matrix(
        self,
        synthesized_record_status_matrix: dict,
        endpoint_identifier: str,
    ) -> None:
        """Update the record_status_matrix"""

        # Note : automatically set all to True / synthesized
        for syn_id in list(synthesized_record_status_matrix.keys()):
            synthesized_record_status_matrix[syn_id][endpoint_identifier] = True

    def get_advice(
        self,
    ) -> dict:
        """Get advice on the next steps (for display in the colrev status)"""

        data_endpoint = "Data operation [prisma data endpoint]: "

        path_str = ",".join(
            [
                str(x.relative_to(self.review_manager.path))
                for x in self.settings.diagram_path
            ]
        )
        advice = {
            "msg": f"{data_endpoint}"
            + "\n    - The PRISMA diagram is created automatically "
            + f"({path_str})",
            "detailed_msg": "TODO",
        }
        return advice
