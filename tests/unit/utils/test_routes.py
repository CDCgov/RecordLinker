import fastapi
import pytest

from recordlinker import models
from recordlinker.utils import routes as utils


def test_algorithm_or_422(session):
    algo1 = models.Algorithm(label="basic", is_default=True, description="First algorithm")
    algo2 = models.Algorithm(label="enhanced", description="Second algorithm")
    session.add(algo1)
    session.add(algo2)
    session.commit()

    alg = utils.algorithm_or_422(session, "enhanced")
    assert alg.label == "enhanced"
    alg = utils.algorithm_or_422(session, None)
    assert alg.label == "basic"
    with pytest.raises(fastapi.HTTPException) as exc:
        utils.algorithm_or_422(session, "invalid")
        assert exc.value.status_code == 422


def test_fhir_record_or_422():
    with pytest.raises(fastapi.HTTPException) as exc:
        utils.fhir_record_or_422({})
        assert exc.value.status_code == 422
    with pytest.raises(fastapi.HTTPException) as exc:
        utils.fhir_record_or_422({"resourceType": "Patient"})
        assert exc.value.status_code == 422
    with pytest.raises(fastapi.HTTPException) as exc:
        utils.fhir_record_or_422({"entry": []})
        assert exc.value.status_code == 422
    with pytest.raises(fastapi.HTTPException) as exc:
        utils.fhir_record_or_422({"entry": [{"resource": {"resourceType": "Encounter"}}]})
        assert exc.value.status_code == 422
    record = utils.fhir_record_or_422(
        {"entry": [{"resource": {"resourceType": "Patient", "id": "1"}}]}
    )
    assert record.external_id == "1"
