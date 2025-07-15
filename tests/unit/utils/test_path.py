import pathlib
import tempfile
import unittest.mock

import pytest

from recordlinker.utils import path as utils


def test_code_root():
    root = utils.code_root()
    assert root.name == "recordlinker"


def test_code_root_not_found():
    with unittest.mock.patch("pathlib.Path.resolve") as mock_resolve:
        mock_resolve.return_value = pathlib.Path("/")
        with pytest.raises(FileNotFoundError):
            utils.code_root()

def test_repo_root():
    root = utils.repo_root()
    assert root is not None


def test_repo_root_not_found():
    with unittest.mock.patch("pathlib.Path.resolve") as mock_resolve:
        mock_resolve.return_value = pathlib.Path("/")
        root = utils.repo_root()
        assert root is None


def test_rel_path():
    assert utils.rel_path(utils.code_root()).endswith("src/recordlinker")


def test_read_json_relative():
    tmp = utils.code_root() / "test.json"
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
