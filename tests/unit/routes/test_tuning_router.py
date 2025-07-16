"""
unit.routes.test_tuning_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.tuning_router module.
"""

import time
import unittest.mock as mock
import uuid

from conftest import load_test_json_asset

from recordlinker import config
from recordlinker.models import tuning as models


class TestCreate:
    def path(self, client):
        return client.app.url_path_for("create-tuning-job")
    
    def seed(self, client):
        return client.app.url_path_for("seed-batch")

    def test_already_in_progress(self, monkeypatch, client):
        client.session.add(
            models.TuningJob(
                status=models.TuningStatus.RUNNING,
                params={
                    "true_match_pairs_requested": 1000,
                    "non_match_pairs_requested": 1000,
                    "non_match_sample_requested": 10000,
                },
            )
        )
        client.session.commit()

        monkeypatch.setattr(config.settings, "tuning_job_timeout", 300)
        resp = client.post(self.path(client))
        assert resp.status_code == 409

    def test_create_timeout(self, monkeypatch, client):
        def mock_sleep(*args, **kwargs):
            time.sleep(0.1)

        monkeypatch.setattr(config.settings, "tuning_job_timeout", 0.01)
        monkeypatch.setattr(config.settings, "tuning_true_match_pairs", 1000)
        monkeypatch.setattr(config.settings, "tuning_non_match_pairs", 1000)
        monkeypatch.setattr(config.settings, "tuning_non_match_sample", 10000)
        with (
            mock.patch("recordlinker.routes.tuning_router.tune") as mock_tune,
            mock.patch("recordlinker.tuning.base.get_session_manager") as mock_session_t,
            mock.patch("recordlinker.routes.tuning_router.get_session_manager") as mock_session_r,
        ):
            mock_tune.side_effect = mock_sleep
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
            assert job.results["details"] == "job timed out"

    @mock.patch('recordlinker.tuning.base.default_algorithm')
    def test_create(self, patched_algo, default_algorithm, monkeypatch, client):
        # Need to seed DB first so we don't error out on randomly sampling
        # non-match pairs
        # NOTE: This file doesn't actually have enough patients or clusters to meet
        # the requested sample or volume, so this functions as the creation test
        # and coverage for logger warnings
        data = load_test_json_asset("100_cluster_tuning_test.json.gz")
        client.post(self.seed(client), json=data)

        patched_algo.return_value = default_algorithm

        monkeypatch.setattr(config.settings, "tuning_true_match_pairs", 1000)
        monkeypatch.setattr(config.settings, "tuning_non_match_pairs", 1000)
        monkeypatch.setattr(config.settings, "tuning_non_match_sample", 10000)
        with mock.patch("recordlinker.tuning.base.get_session_manager") as mock_session_b, \
                mock.patch("recordlinker.routes.tuning_router.get_session_manager") as mock_session_r:
            mock_session_b.return_value = client.session
            mock_session_r.return_value = client.session
            resp = client.post(self.path(client))
            job = client.session.query(models.TuningJob).first()

            assert resp.status_code == 202
            assert resp.json()["id"] == str(job.id)
            assert resp.json()["status"] == "pending"
            # This isn't intuitive, but when the job is created its placed in the pending state.
            # However, once the job starts processing in the background job, its immediately
            # placed in the running state
            assert job.status == models.TuningStatus.COMPLETED
            assert resp.json()["params"] == {
                "true_match_pairs_requested": 1000,
                "non_match_pairs_requested": 1000,
                "non_match_sample_requested": 10000,
            }
            assert resp.json()["results"] is None
            assert resp.json()["status_url"] == f"http://testserver/api/tuning/{job.id}"


class TestError:
    def path(self, client):
        return client.app.url_path_for("create-tuning-job")
    
    def seed(self, client):
        return client.app.url_path_for("seed-batch")
    
    def test_too_few_true_match(self, monkeypatch, client):
        monkeypatch.setattr(config.settings, "tuning_true_match_pairs", 1)
        with mock.patch("recordlinker.tuning.base.get_session_manager") as mock_session_b, \
                mock.patch("recordlinker.routes.tuning_router.get_session_manager") as mock_session_r:
            mock_session_b.return_value = client.session
            mock_session_r.return_value = client.session
            client.post(self.path(client))
            job = client.session.query(models.TuningJob).first()
            assert job.status == models.TuningStatus.FAILED
            assert "few true match pairs requested" in job.results['details']
    
    def test_too_few_neg_samples(self, monkeypatch, client):
        monkeypatch.setattr(config.settings, "tuning_non_match_sample", 1)
        with mock.patch("recordlinker.tuning.base.get_session_manager") as mock_session_b, \
                mock.patch("recordlinker.routes.tuning_router.get_session_manager") as mock_session_r:
            mock_session_b.return_value = client.session
            mock_session_r.return_value = client.session
            client.post(self.path(client))
            job = client.session.query(models.TuningJob).first()
            assert job.status == models.TuningStatus.FAILED
            assert "few non match samples requested" in job.results['details']
    
    def test_too_few_neg_pairs(self, monkeypatch, client):
        monkeypatch.setattr(config.settings, "tuning_non_match_pairs", 1)
        with mock.patch("recordlinker.tuning.base.get_session_manager") as mock_session_b, \
                mock.patch("recordlinker.routes.tuning_router.get_session_manager") as mock_session_r:
            mock_session_b.return_value = client.session
            mock_session_r.return_value = client.session
            client.post(self.path(client))
            job = client.session.query(models.TuningJob).first()
            assert job.status == models.TuningStatus.FAILED
            assert "few non match pairs requested" in job.results['details']
    
    def test_db_empty(self, monkeypatch, client):
        monkeypatch.setattr(config.settings, "tuning_true_match_pairs", 1000)
        monkeypatch.setattr(config.settings, "tuning_non_match_pairs", 1000)
        monkeypatch.setattr(config.settings, "tuning_non_match_sample", 10000)
        with mock.patch("recordlinker.tuning.base.get_session_manager") as mock_session_b, \
                mock.patch("recordlinker.routes.tuning_router.get_session_manager") as mock_session_r:
            mock_session_b.return_value = client.session
            mock_session_r.return_value = client.session
            client.post(self.path(client))
            job = client.session.query(models.TuningJob).first()
            assert job.status == models.TuningStatus.FAILED
            assert "MPI contains no patient data" in job.results['details']
    

    def test_all_singleton_patients(self, monkeypatch, client):
        # Modify the DB seed so that there's only one patient in each cluster
        data = load_test_json_asset("100_cluster_tuning_test.json.gz")
        new_clusters = []
        for c in data["clusters"]:
            c["records"] = [c["records"][0]]
            new_clusters.append(c)
        data["clusters"] = new_clusters
        client.post(self.seed(client), json=data)

        monkeypatch.setattr(config.settings, "tuning_true_match_pairs", 1000)
        monkeypatch.setattr(config.settings, "tuning_non_match_pairs", 1000)
        monkeypatch.setattr(config.settings, "tuning_non_match_sample", 10000)
        with mock.patch("recordlinker.tuning.base.get_session_manager") as mock_session_b, \
                mock.patch("recordlinker.routes.tuning_router.get_session_manager") as mock_session_r:
            mock_session_b.return_value = client.session
            mock_session_r.return_value = client.session
            client.post(self.path(client))
            job = client.session.query(models.TuningJob).first()
            assert job.status == models.TuningStatus.FAILED
            assert "MPI has person structure that does not support tuning" in job.results['details']


    def test_monolith_cluster(self, monkeypatch, client):
        # Modify the DB seed so that there's only Person cluster to which all patients belong
        data = load_test_json_asset("100_cluster_tuning_test.json.gz")
        patient_records = []
        for c in data["clusters"]:
            patient_records += c["records"]
        data["clusters"] = [data["clusters"][0]]
        data["clusters"][0]["records"] = patient_records
        client.post(self.seed(client), json=data)

        monkeypatch.setattr(config.settings, "tuning_true_match_pairs", 1000)
        monkeypatch.setattr(config.settings, "tuning_non_match_pairs", 1000)
        monkeypatch.setattr(config.settings, "tuning_non_match_sample", 10000)
        with mock.patch("recordlinker.tuning.base.get_session_manager") as mock_session_b, \
                mock.patch("recordlinker.routes.tuning_router.get_session_manager") as mock_session_r:
            mock_session_b.return_value = client.session
            mock_session_r.return_value = client.session
            client.post(self.path(client))
            job = client.session.query(models.TuningJob).first()
            assert job.status == models.TuningStatus.FAILED
            assert "MPI has person structure that does not support tuning" in job.results['details']
            assert ", have 1" in job.results["details"]


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
                "true_match_pairs_requested": 1000,
                "non_match_pairs_requested": 1000,
                "non_match_sample_requested": 10000,
            },
        )
        client.session.add(obj)
        client.session.commit()

        resp = client.get(self.path(client, obj.id))
        assert resp.status_code == 200
        assert resp.json()["id"] == str(obj.id)
        assert resp.json()["status"] == "running"
        assert resp.json()["params"] == {
            "true_match_pairs_requested": 1000,
            "non_match_pairs_requested": 1000,
            "non_match_sample_requested": 10000,
        }
        assert resp.json()["results"] is None
        assert resp.json()["started_at"] == obj.started_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert resp.json()["finished_at"] is None
        assert resp.json()["status_url"] == f"http://testserver/api/tuning/{obj.id}"
