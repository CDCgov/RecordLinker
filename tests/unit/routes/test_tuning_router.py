"""
unit.routes.test_tuning_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.tuning_router module.
"""

import unittest.mock as mock
import uuid

from recordlinker import config
from recordlinker.models import tuning as models


class TestCreate:
    def path(self, client):
        return client.app.url_path_for("create-tuning-job")

    def test_already_in_progress(self, monkeypatch, client):
        client.session.add(
            models.TuningJob(
                status=models.TuningStatus.RUNNING,
                params={
                    "true_match_pairs_requested": 1,
                    "non_match_pairs_requested": 1,
                    "non_match_sample_requested": 1,
                },
            )
        )
        client.session.commit()

        monkeypatch.setattr(config.settings, "tuning_job_timeout", 300)
        resp = client.post(self.path(client))
        assert resp.status_code == 409

    def test_create_timeout(self, monkeypatch, client):
        monkeypatch.setattr(config.settings, "tuning_job_timeout", 0)
        monkeypatch.setattr(config.settings, "tuning_true_match_pairs", 1)
        monkeypatch.setattr(config.settings, "tuning_non_match_pairs", 1)
        monkeypatch.setattr(config.settings, "tuning_non_match_sample", 1)
        with (
            mock.patch("recordlinker.tuning.base.get_session_manager") as mock_session_t,
            mock.patch("recordlinker.routes.tuning_router.get_session_manager") as mock_session_r,
        ):
            mock_session_r.return_value = client.session
            mock_session_t.return_value = client.session
            resp = client.post(self.path(client))
            job = client.session.query(models.TuningJob).first()

            assert resp.status_code == 202
            assert resp.json()["id"] == str(job.id)
            assert resp.json()["status"] == "pending"
            # This isn't intuitive, but when the job is created its placed in the pending state.
            # However, once the job starts processing in the background job, its immediately
            # canceled because of a timeout
            assert job.status == models.TuningStatus.FAILED

    def test_create(self, monkeypatch, client):
        monkeypatch.setattr(config.settings, "tuning_true_match_pairs", 1)
        monkeypatch.setattr(config.settings, "tuning_non_match_pairs", 1)
        monkeypatch.setattr(config.settings, "tuning_non_match_sample", 1)
        with mock.patch("recordlinker.tuning.base.get_session_manager") as mock_session:
            mock_session.return_value = client.session
            resp = client.post(self.path(client))
            job = client.session.query(models.TuningJob).first()

            assert resp.status_code == 202
            assert resp.json()["id"] == str(job.id)
            assert resp.json()["status"] == "pending"
            # This isn't intuitive, but when the job is created its placed in the pending state.
            # However, once the job starts processing in the background job, its immediately
            # placed in the running state
            assert job.status == models.TuningStatus.RUNNING
            assert resp.json()["params"] == {
                "true_match_pairs_requested": 1,
                "non_match_pairs_requested": 1,
                "non_match_sample_requested": 1,
            }
            assert resp.json()["results"] is None
            assert resp.json()["status_url"] == f"http://testserver/api/tuning/{job.id}"


class TestGet:
    def path(self, client, job_id):
        return client.app.url_path_for("get-tuning-job", job_id=job_id)

    def test_not_found(self, client):
        resp = client.get(self.path(client, uuid.uuid4()))
        assert resp.status_code == 404

    def test_get(self, client):
        obj = models.TuningJob(
            status=models.TuningStatus.RUNNING,
            params={
                "true_match_pairs_requested": 1,
                "non_match_pairs_requested": 1,
                "non_match_sample_requested": 1,
            },
        )
        client.session.add(obj)
        client.session.commit()

        resp = client.get(self.path(client, obj.id))
        assert resp.status_code == 200
        assert resp.json()["id"] == str(obj.id)
        assert resp.json()["status"] == "running"
        assert resp.json()["params"] == {
            "true_match_pairs_requested": 1,
            "non_match_pairs_requested": 1,
            "non_match_sample_requested": 1,
        }
        assert resp.json()["results"] is None
        assert resp.json()["started_at"] == obj.started_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert resp.json()["finished_at"] is None
        assert resp.json()["status_url"] == f"http://testserver/api/tuning/{obj.id}"
