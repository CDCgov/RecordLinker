"""
unit.database.test_tuning_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.database.tuning_service module.
"""

import datetime
import uuid

from recordlinker.database import tuning_service
from recordlinker.models import tuning as models
from recordlinker.schemas import tuning as schemas
from recordlinker.utils.datetime import now_utc_no_ms


class TestStartJob:
    def test(self, session):
        params = schemas.TuningParams(true_match_pairs=1, non_match_pairs=1)
        job = tuning_service.start_job(session, params)
        assert job.status == models.TuningStatus.PENDING
        assert job.params == params
        assert job.results is None
        assert job.started_at <= now_utc_no_ms()
        assert job.finished_at is None

        obj = session.get(models.TuningJob, job.id)
        assert obj.status == models.TuningStatus.PENDING
        assert obj.params == {"true_match_pairs": 1, "non_match_pairs": 1}
        assert obj.results is None
        assert obj.started_at <= now_utc_no_ms()
        assert obj.finished_at is None


class TestGetJob:
    def test_not_found(self, session):
        job = tuning_service.get_job(session, uuid.uuid4())
        assert job is None

    def test_found(self, session):
        obj = models.TuningJob(
            status=models.TuningStatus.FAILED,
            params={"true_match_pairs": 1, "non_match_pairs": 1},
            results={"details": "test failed"},
            started_at=datetime.datetime(2025, 1, 1, 0, 0, 0),
            finished_at=datetime.datetime(2025, 1, 1, 0, 0, 10),
        )
        session.add(obj)
        session.commit()

        job = tuning_service.get_job(session, obj.id)
        assert job is not None
        assert job.id == obj.id
        assert job.status == models.TuningStatus.FAILED
        assert job.params == schemas.TuningParams(true_match_pairs=1, non_match_pairs=1)
        assert job.results == schemas.TuningResults(details="test failed")
        assert job.duration == datetime.timedelta(seconds=10)


class TestUpdateJob:
    def test_set_results(self, session):
        obj = models.TuningJob(
            status=models.TuningStatus.PENDING,
            params={"true_match_pairs": 1, "non_match_pairs": 1},
            started_at=now_utc_no_ms(),
        )
        session.add(obj)
        session.commit()

        job = schemas.TuningJob.model_validate(obj)
        results = schemas.TuningResults(details="running")
        job = tuning_service.update_job(session, job, models.TuningStatus.RUNNING, results)
        assert job.status == models.TuningStatus.RUNNING
        assert job.results == results

        obj = session.get(models.TuningJob, job.id)
        assert obj.status == models.TuningStatus.RUNNING
        assert obj.params == {"true_match_pairs": 1, "non_match_pairs": 1}
        assert obj.results == {
            "dataset_size": 0,
            "true_matches_found": 0,
            "non_matches_found": 0,
            "log_odds": [],
            "details": "running",
        }
        assert obj.started_at <= now_utc_no_ms().replace(tzinfo=None)
        assert obj.finished_at is None

    def test_completed(self, session):
        obj = models.TuningJob(
            status=models.TuningStatus.PENDING,
            params={"true_match_pairs": 1, "non_match_pairs": 1},
            started_at=now_utc_no_ms(),
        )
        session.add(obj)
        session.commit()

        job = schemas.TuningJob.model_validate(obj)
        results = schemas.TuningResults(details="completed")
        job = tuning_service.update_job(session, job, models.TuningStatus.COMPLETED, results)
        assert job.status == models.TuningStatus.COMPLETED
        assert job.results == results

        obj = session.get(models.TuningJob, job.id)
        assert obj.status == models.TuningStatus.COMPLETED
        assert obj.params == {"true_match_pairs": 1, "non_match_pairs": 1}
        assert obj.results == {
            "dataset_size": 0,
            "true_matches_found": 0,
            "non_matches_found": 0,
            "log_odds": [],
            "details": "completed",
        }
        assert obj.started_at <= now_utc_no_ms().replace(tzinfo=None)
        assert obj.finished_at >= obj.started_at

    def test_failed(self, session):
        obj = models.TuningJob(
            status=models.TuningStatus.FAILED,
            params={"true_match_pairs": 1, "non_match_pairs": 1},
            started_at=now_utc_no_ms(),
        )
        session.add(obj)
        session.commit()

        job = schemas.TuningJob.model_validate(obj)
        results = schemas.TuningResults(details="failed")
        job = tuning_service.update_job(session, job, models.TuningStatus.FAILED, results)
        assert job.status == models.TuningStatus.FAILED
        assert job.results == results

        obj = session.get(models.TuningJob, job.id)
        assert obj.status == models.TuningStatus.FAILED
        assert obj.params == {"true_match_pairs": 1, "non_match_pairs": 1}
        assert obj.results == {
            "dataset_size": 0,
            "true_matches_found": 0,
            "non_matches_found": 0,
            "log_odds": [],
            "details": "failed",
        }
        assert obj.started_at <= now_utc_no_ms().replace(tzinfo=None)
        assert obj.finished_at >= obj.started_at
