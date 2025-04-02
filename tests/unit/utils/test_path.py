import pathlib
import tempfile
import unittest.mock

import pytest

from recordlinker.utils import path as utils


def test_project_root():
    root = utils.project_root()
    assert root.name == "recordlinker"


def test_project_root_not_found():
    with unittest.mock.patch("pathlib.Path.resolve") as mock_resolve:
        mock_resolve.return_value = pathlib.Path("/")
        with pytest.raises(FileNotFoundError):
            utils.project_root()


def test_read_json_relative():
    tmp = utils.project_root() / "test.json"
    with open(tmp, "w") as fobj:
        fobj.write('{"key": "value"}')
    assert utils.read_json("test.json") == {"key": "value"}
    tmp.unlink()


def test_read_json_absolute():
    tmp = tempfile.NamedTemporaryFile(suffix=".json")
    with open(tmp.name, "w") as fobj:
        fobj.write('{"key": "value"}')
    assert utils.read_json(tmp.name) == {"key": "value"}
    tmp.close()
