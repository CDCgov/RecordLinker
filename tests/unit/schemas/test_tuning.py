"""
unit.schemas.test_tuning.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.schemas.tuning module.
"""

import datetime

from recordlinker.schemas.tuning import TuningJob
from recordlinker.schemas.tuning import TuningParams


class TestTuningJob:
    def test_duration(self):
        job = TuningJob(
            params=TuningParams(
                true_match_pairs_requested=1,
                non_match_pairs_requested=1,
                non_match_sample_requested=1,
            )
        )
        assert job.duration is None
        job.finished_at = job.started_at + datetime.timedelta(seconds=4)
        assert job.duration.total_seconds() == 4
