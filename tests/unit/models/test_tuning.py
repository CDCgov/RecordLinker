"""
unit.models.test_tuning.py
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.models.tuning module.
"""

import datetime
import unittest.mock

from recordlinker.models import tuning as models


class TestTuningJob:
    def test_duration(self, session):
        with unittest.mock.patch("recordlinker.models.tuning.now_utc_no_ms") as mock_now:
            mock_now.return_value = datetime.datetime(2025, 1, 1, 0, 5, 0)
            job = models.TuningJob(started_at=datetime.datetime(2025, 1, 1, 0, 0, 0))
            assert job.duration.total_seconds() == 300
            job.finished_at = datetime.datetime(2025, 1, 1, 0, 2, 0)
            assert job.duration.total_seconds() == 120
