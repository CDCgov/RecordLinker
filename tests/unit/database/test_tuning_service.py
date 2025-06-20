"""
unit.database.test_tuning_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.database.tuning_service module.
"""

import datetime
import uuid

import pytest

from recordlinker.database import tuning_service
from recordlinker.models import tuning as models
from recordlinker.schemas import tuning as schemas
from recordlinker.utils.datetime import now_utc_no_ms


class TestStartJob:
    def test(self, session):
        params = schemas.TuningParams(
            true_match_pairs_requested=1, non_match_pairs_requested=1, non_match_sample_requested=1
        )
        job = tuning_service.start_job(session, params)
        assert job.status == models.TuningStatus.PENDING
        assert job.params == params
        assert job.results is None
        assert job.started_at <= now_utc_no_ms()
        assert job.finished_at is None

        obj = session.get(models.TuningJob, job.id)
        assert obj.status == models.TuningStatus.PENDING
        assert obj.params == {
            "true_match_pairs_requested": 1,
            "non_match_pairs_requested": 1,
            "non_match_sample_requested": 1,
        }
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
            params={
                "true_match_pairs_requested": 1,
                "non_match_pairs_requested": 1,
                "non_match_sample_requested": 1,
            },
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
        assert job.params == schemas.TuningParams(
            true_match_pairs_requested=1, non_match_pairs_requested=1, non_match_sample_requested=1
        )
        assert job.results == schemas.TuningResults(details="test failed")


class TestUpdateJob:
    def test_not_found(self, session):
        job = schemas.TuningJob(
            params=schemas.TuningParams(
                true_match_pairs_requested=1,
                non_match_pairs_requested=1,
                non_match_sample_requested=1,
            )
        )
        with pytest.raises(ValueError):
            tuning_service.update_job(session, job, models.TuningStatus.RUNNING)

    def test_set_results(self, session):
        obj = models.TuningJob(
            status=models.TuningStatus.PENDING,
            params={
                "true_match_pairs_requested": 1,
                "non_match_pairs_requested": 1,
                "non_match_sample_requested": 1,
            },
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
        assert obj.params == {
            "true_match_pairs_requested": 1,
            "non_match_pairs_requested": 1,
            "non_match_sample_requested": 1,
        }
        assert obj.results == {
            "true_match_pairs_used": 0,
            "non_match_pairs_used": 0,
            "non_match_sample_used": 0,
            "log_odds": [],
            "passes": [],
            "details": "running",
        }
        assert obj.started_at <= now_utc_no_ms()
        assert obj.finished_at is None

    def test_completed(self, session):
        obj = models.TuningJob(
            status=models.TuningStatus.PENDING,
            params={
                "true_match_pairs_requested": 1,
                "non_match_pairs_requested": 1,
                "non_match_sample_requested": 1,
            },
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
        assert obj.params == {
            "true_match_pairs_requested": 1,
            "non_match_pairs_requested": 1,
            "non_match_sample_requested": 1,
        }
        assert obj.results == {
            "true_match_pairs_used": 0,
            "non_match_pairs_used": 0,
            "non_match_sample_used": 0,
            "log_odds": [],
            "passes": [],
            "details": "completed",
        }
        assert obj.started_at <= now_utc_no_ms()
        assert obj.finished_at >= obj.started_at

    def test_failed(self, session):
        obj = models.TuningJob(
            status=models.TuningStatus.FAILED,
            params={
                "true_match_pairs_requested": 1,
                "non_match_pairs_requested": 1,
                "non_match_sample_requested": 1,
            },
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
        assert obj.params == {
            "true_match_pairs_requested": 1,
            "non_match_pairs_requested": 1,
            "non_match_sample_requested": 1,
        }
        assert obj.results == {
            "true_match_pairs_used": 0,
            "non_match_pairs_used": 0,
            "non_match_sample_used": 0,
            "log_odds": [],
            "passes": [],
            "details": "failed",
        }
        assert obj.started_at <= now_utc_no_ms()
        assert obj.finished_at >= obj.started_at


class TestFailJob:
    def test_missing_job(self, session):
        assert tuning_service.fail_job(session, uuid.uuid4(), "missing") is None
        assert session.query(models.TuningJob).count() == 0

    def test_update(self, session):
        obj = models.TuningJob(status=models.TuningStatus.PENDING, params={})
        session.add(obj)
        session.commit()

        assert tuning_service.fail_job(session, obj.id, "failed") is None
        assert session.query(models.TuningJob).count() == 1

        obj = session.get(models.TuningJob, obj.id)
        assert obj.status == models.TuningStatus.FAILED
        assert obj.results == {
            "true_match_pairs_used": 0,
            "non_match_pairs_used": 0,
            "non_match_sample_used": 0,
            "log_odds": [],
            "passes": [],
            "details": "failed",
        }
        assert obj.finished_at >= obj.started_at


class TestGetActiveJob:
    def test_none(self, session):
        assert tuning_service.get_active_jobs(session) == []

    def test_no_active(self, session):
        session.add(models.TuningJob(status=models.TuningStatus.COMPLETED, params={}))
        session.add(models.TuningJob(status=models.TuningStatus.FAILED, params={}))
        session.commit()

        assert tuning_service.get_active_jobs(session) == []

    def test_jobs_to_cancel(self, session):
        session.add(
            models.TuningJob(
                status=models.TuningStatus.PENDING,
                params={
                    "true_match_pairs_requested": 1,
                    "non_match_pairs_requested": 1,
                    "non_match_sample_requested": 1,
                },
                started_at=datetime.datetime(2025, 1, 1, 0, 0, 0),
            )
        )
        session.commit()

        assert tuning_service.get_active_jobs(session) == []
        obj = session.query(models.TuningJob).first()
        assert obj.status == models.TuningStatus.FAILED
        assert obj.params == {
            "true_match_pairs_requested": 1,
            "non_match_pairs_requested": 1,
            "non_match_sample_requested": 1,
        }
        assert obj.results == {
            "true_match_pairs_used": 0,
            "non_match_pairs_used": 0,
            "non_match_sample_used": 0,
            "log_odds": [],
            "passes": [],
            "details": "canceled incomplete job",
        }
        assert obj.started_at == datetime.datetime(
            2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        )
        assert obj.finished_at > obj.started_at

    def test_jobs(self, session):
        session.add(
            models.TuningJob(
                status=models.TuningStatus.PENDING,
                params={
                    "true_match_pairs_requested": 1,
                    "non_match_pairs_requested": 1,
                    "non_match_sample_requested": 1,
                },
            )
        )
        session.add(
            models.TuningJob(
                status=models.TuningStatus.RUNNING,
                params={
                    "true_match_pairs_requested": 1,
                    "non_match_pairs_requested": 1,
                    "non_match_sample_requested": 1,
                },
            )
        )

        jobs = tuning_service.get_active_jobs(session)
        assert len(jobs) == 2
        statuses = {job.status for job in jobs}
        assert statuses == {models.TuningStatus.PENDING, models.TuningStatus.RUNNING}
