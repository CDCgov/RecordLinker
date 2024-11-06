"""
recordlinker.openapi_schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module exports the OpenAPI schema for the Record Linker service.
"""

import json
import sys
import typing

from fastapi.openapi.utils import get_openapi

from recordlinker import main


def export_json(file: typing.TextIO):
    """
    Export the OpenAPI schema to a JSON file.
    """
    json.dump(
        get_openapi(
            title=main.app.title,
            version=main.app.version,
            openapi_version=main.app.openapi_version,
            description=main.app.description,
            routes=main.app.routes,
            license_info=main.app.license_info,
            contact=main.app.contact,
        ),
        file,
    )


if __name__ == "__main__":
    export_json(sys.stdout)
