"""
unit.models.test_tuning.py
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.models.tuning module.
"""

import datetime

from recordlinker.models import tuning as models


class TestTuningJob:
    def test_started_at_timezone(self, session):
        kwargs = {
            "status": models.TuningStatus.PENDING,
            "params": {},
        }
        session.add(models.TuningJob(**kwargs))
        session.commit()

        job = session.query(models.TuningJob).first()
        assert job.started_at.tzinfo == datetime.timezone.utc

    def test_finished_at_timezone(self, session):
        kwargs = {
            "status": models.TuningStatus.PENDING,
            "params": {},
            "finished_at": datetime.datetime.now(tz=datetime.timezone.utc),
        }
        session.add(models.TuningJob(**kwargs))
        session.commit()

        job = session.query(models.TuningJob).first()
        assert job.finished_at.tzinfo == datetime.timezone.utc
