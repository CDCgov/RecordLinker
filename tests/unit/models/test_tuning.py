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


class TestTZDateTime:
    def test_naive_datetime_becomes_utc(self, session):
        naive_dt = datetime.datetime(2024, 1, 1, 12, 0, 0)  # Naive
        obj = models.TuningJob(status=models.TuningStatus.PENDING, params={}, started_at=naive_dt)
        session.add(obj)
        session.commit()

        obj = session.query(models.TuningJob).first()
        assert obj.started_at.tzinfo is not None
        assert obj.started_at.tzinfo.utcoffset(obj.started_at) == datetime.timedelta(0)

    def test_aware_datetime_preserved_as_utc(self, session):
        aware_dt = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        obj = models.TuningJob(status=models.TuningStatus.PENDING, params={}, started_at=aware_dt)
        session.add(obj)
        session.commit()

        obj = session.query(models.TuningJob).first()
        assert obj.started_at == aware_dt
        assert obj.started_at.tzinfo == datetime.timezone.utc

    def test_non_utc_converted_to_utc(self, session):
        est = datetime.timezone(datetime.timedelta(hours=-5))
        dt_est = datetime.datetime(2024, 1, 1, 7, 0, 0, tzinfo=est)
        obj = models.TuningJob(status=models.TuningStatus.PENDING, params={}, started_at=dt_est)
        session.add(obj)
        session.commit()

        obj = session.query(models.TuningJob).first()
        assert obj.started_at.hour == 12
        assert obj.started_at.tzinfo == datetime.timezone.utc
