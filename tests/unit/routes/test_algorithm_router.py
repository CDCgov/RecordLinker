"""
unit.routes.test_algorithm_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.algorithm_router module.
"""

from recordlinker import models


class TestListAlgorithms:
    def test_list(self, client):
        algo1 = models.Algorithm(label="basic", is_default=True, description="First algorithm")
        algo2 = models.Algorithm(label="enhanced", description="Second algorithm")
        client.session.add(algo1)
        client.session.add(algo2)
        client.session.commit()

        response = client.get("/algorithm")
        assert response.status_code == 200
        assert response.json() == [
            {
                "label": "basic",
                "is_default": True,
                "description": "First algorithm",
                "pass_count": 0,
            },
            {
                "label": "enhanced",
                "is_default": False,
                "description": "Second algorithm",
                "pass_count": 0,
            },
        ]


class TestGetAlgorithm:
    def test_404(self, client):
        response = client.get("/algorithm/unknown")
        assert response.status_code == 404

    def test_get(self, client):
        algo = models.Algorithm(
            label="basic",
            description="First algorithm",
            passes=[
                models.AlgorithmPass(
                    blocking_keys=[
                        "BIRTHDATE",
                    ],
                    evaluators={
                        "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_fuzzy_string",
                    },
                    rule="func:recordlinker.linking.matchers.eval_perfect_match",
                    cluster_ratio=0.5,
                )
            ],
        )
        client.session.add(algo)
        client.session.commit()

        response = client.get(f"/algorithm/{algo.label}")
        assert response.status_code == 200
        assert response.json() == {
            "label": "basic",
            "is_default": False,
            "description": "First algorithm",
            "passes": [
                {
                    "blocking_keys": ["BIRTHDATE"],
                    "evaluators": {
                        "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_fuzzy_string",
                    },
                    "rule": "func:recordlinker.linking.matchers.eval_perfect_match",
                    "cluster_ratio": 0.5,
                    "kwargs": {},
                }
            ],
        }


class TestCreateAlgorithm:
    def test_invalid_data(self, client):
        response = client.post("/algorithm", json={})
        assert response.status_code == 422

    def test_exsiting_default(self, client):
        algo = models.Algorithm(label="basic", is_default=True, description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        payload = {
            "label": "advanced",
            "is_default": True,
            "description": "Advanced algorithm",
            "passes": [],
        }
        response = client.post("/algorithm", json=payload)
        assert response.status_code == 422

    def test_create(self, client):
        payload = {
            "label": "basic",
            "description": "First algorithm",
            "passes": [
                {
                    "blocking_keys": [
                        "BIRTHDATE",
                    ],
                    "evaluators": {
                        "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_fuzzy_string",
                    },
                    "rule": "func:recordlinker.linking.matchers.eval_perfect_match",
                    "cluster_ratio": 0.5,
                }
            ],
        }
        response = client.post("/algorithm", json=payload)
        assert response.status_code == 201

        algo = (
            client.session.query(models.Algorithm).filter(models.Algorithm.label == "basic").first()
        )
        assert algo.label == "basic"
        assert algo.is_default is False
        assert algo.description == "First algorithm"
        assert len(algo.passes) == 1
        assert algo.passes[0].blocking_keys == ["BIRTHDATE"]
        assert algo.passes[0].evaluators == {
            "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_fuzzy_string"
        }
        assert algo.passes[0].rule == "func:recordlinker.linking.matchers.eval_perfect_match"
        assert algo.passes[0].cluster_ratio == 0.5
        assert algo.passes[0].kwargs == {}


class TestUpdateAlgorithm:
    def test_404(self, client):
        payload = {
            "label": "basic",
            "description": "First algorithm",
            "passes": [],
        }
        response = client.put("/algorithm/unknown", json=payload)
        assert response.status_code == 404

    def test_invalid_data(self, client):
        algo = models.Algorithm(label="basic", description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        response = client.put("/algorithm/basic", json={})
        assert response.status_code == 422

    def test_exsiting_default(self, client):
        algo1 = models.Algorithm(label="default", is_default=True, description="algorithm")
        algo2 = models.Algorithm(label="basic", is_default=False, description="First algorithm")
        client.session.add(algo1)
        client.session.add(algo2)
        client.session.commit()

        payload = {
            "label": "basic",
            "is_default": True,
            "description": "new default algorithm",
            "passes": [],
        }
        response = client.post("/algorithm", json=payload)
        assert response.status_code == 422


    def test_update(self, client):
        algo = models.Algorithm(
            label="basic",
            description="First algorithm",
            passes=[]
        )
        client.session.add(algo)
        client.session.commit()

        payload = {
            "label": "basic",
            "description": "Updated algorithm",
            "passes": [
                {
                    "blocking_keys": [
                        "BIRTHDATE",
                    ],
                    "evaluators": {
                        "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_fuzzy_string",
                    },
                    "rule": "func:recordlinker.linking.matchers.eval_perfect_match",
                    "cluster_ratio": 0.5,
                }
            ],
        }
        response = client.put("/algorithm/basic", json=payload)
        assert response.status_code == 200

        algo = (
            client.session.query(models.Algorithm).filter(models.Algorithm.label == "basic").first()
        )
        assert algo.label == "basic"
        assert algo.is_default is False
        assert algo.description == "Updated algorithm"
        assert len(algo.passes) == 1
        assert algo.passes[0].blocking_keys == ["BIRTHDATE"]
        assert algo.passes[0].evaluators == {
            "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_fuzzy_string"
        }
        assert algo.passes[0].rule == "func:recordlinker.linking.matchers.eval_perfect_match"
        assert algo.passes[0].cluster_ratio == 0.5
        assert algo.passes[0].kwargs == {}


class TestDeleteAlgorithm:
    def test_404(self, client):
        response = client.delete("/algorithm/unknown")
        assert response.status_code == 404

    def test_delete(self, client):
        algo = models.Algorithm(label="basic", description="First algorithm")
        client.session.add(algo)
        client.session.commit()

        response = client.delete("/algorithm/basic")
        assert response.status_code == 204

        algo = (
            client.session.query(models.Algorithm).filter(models.Algorithm.label == "basic").first()
        )
        assert algo is None
