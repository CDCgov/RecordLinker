"""
unit.models.test_algorithm.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.models.algorithm module.
"""

import unittest.mock

import pytest

from recordlinker import config
from recordlinker.models import algorithm as models


class TestAlgorithm:
    def test_single_default_algorithm(self, session):
        """
        Tests that only one algorithm can be default in the Algorithm table
        """
        # first algorithm is_default set to True
        algo1 = models.Algorithm(
            label="Algorithm 1", is_default=True, description="First algorithm"
        )
        session.add(algo1)
        session.commit()

        # create another algorithm and try to set is_default as True
        algo2 = models.Algorithm(
            label="Algorithm 2", is_default=True, description="Second algorithm"
        )
        session.add(algo2)

        with pytest.raises(ValueError, match="There can only be one default algorithm"):
            session.commit()

    def test_set_default_when_none_exists(self, session):
        """
        Tests that you can update an algorithm to be the default if no other default exists
        """
        # is_default set to false
        algo1 = models.Algorithm(
            label="Algorithm 1", is_default=False, description="First algorithm"
        )
        session.add(algo1)
        session.commit()

        # try setting it as the default
        algo1.is_default = True
        session.add(algo1)

        session.commit()

    def test_update_existing_default(self, session):
        """
        Tests that updating the default algorithm do not raise ValueErrors
        """
        algo1 = models.Algorithm(
            label="Algorithm 1", is_default=True, description="First algorithm"
        )
        session.add(algo1)
        session.commit()

        # update the same algorithm
        algo1.description = "Updated algorithm"
        session.add(algo1)

        # should not raise any value errors
        session.commit()


class TestCreateInitialAlgorithms:
    def test_invalid_file(self, monkeypatch, session):
        """
        Tests that an invalid file raises a FileNotFoundError
        """
        monkeypatch.setattr(config.settings, "initial_algorithms", "invalid_file.json")
        with pytest.raises(config.ConfigurationError, match="Error loading initial algorithms"):
            models.create_initial_algorithms(None, session.connection())

    def test_no_default(self, monkeypatch, session):
        """
        Tests that the initial algorithms are created without a default algorithm
        """
        monkeypatch.setattr(config.settings, "initial_algorithms", "file.json")
        with unittest.mock.patch("recordlinker.utils.path.read_json") as read_json:
            read_json.return_value = [{"is_default": False}]
            with pytest.raises(config.ConfigurationError, match="No default algorithm found"):
                models.create_initial_algorithms(None, session.connection())

    def test_invalid_algorithm(self, monkeypatch, session):
        """
        Tests that an invalid algorithm raises a ValueError
        """
        monkeypatch.setattr(config.settings, "initial_algorithms", "file.json")
        with unittest.mock.patch("recordlinker.utils.path.read_json") as read_json:
            read_json.return_value = [{"labell": "Algorithm 1", "is_default": True}]
            with pytest.raises(
                config.ConfigurationError, match="Error creating initial algorithms"
            ):
                models.create_initial_algorithms(None, session.connection())

    def test_create_initial_algorithms(self, monkeypatch, session):
        """
        Tests that the initial algorithms are created
        """
        monkeypatch.setattr(config.settings, "initial_algorithms", "file.json")
        with unittest.mock.patch("recordlinker.utils.path.read_json") as read_json:
            read_json.return_value = [{"label": "Algorithm 1", "is_default": True}]
            models.create_initial_algorithms(None, session.connection())
            assert session.query(models.Algorithm).count() == 1
            assert session.query(models.Algorithm).first().is_default is True
            assert session.query(models.Algorithm).first().label == "Algorithm 1"
