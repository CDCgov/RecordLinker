import io
import json

from recordlinker.utils.openapi_schema import export_json


def test_export_json():
    buffer = io.StringIO()
    export_json(buffer)
    result = json.loads(buffer.getvalue())
    assert result["info"]["title"] == "Record Linker"
