"""add dibbs algorithms

Revision ID: a30b8bbccfdf
Revises: d9eba1bdbad1
Create Date: 2024-09-26 15:10:15.179656

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa

from src.recordlinker.models import Algorithm
from src.recordlinker.models import AlgorithmPass
from src.recordlinker.models import BlockingKey


# revision identifiers, used by Alembic.
revision: str = 'a30b8bbccfdf'
down_revision: Union[str, None] = 'd9eba1bdbad1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FUZZY_THRESHOLDS = {
    "first_name": 0.9,
    "last_name": 0.9,
    "birthdate": 0.95,
    "address": 0.9,
    "city": 0.92,
    "zip": 0.95,
}

LOG_ODDS_SCORES = {
    "address": 8.438284928858774,
    "birthdate": 10.126641103800338,
    "city": 2.438553006137189,
    "first_name": 6.849475906891162,
    "last_name": 6.350720397426025,
    "mrn": 0.3051262572525359,
    "sex": 0.7510419059643679,
    "state": 0.022376768992488694,
    "zip": 4.975031471124867,
}

DIBBS_BASIC = {
    "id": 1,
    "is_default": True,
    "label": "DIBBs Basic algorithm",
    "description": "DIBBs Enhanced algorithm description"   #TODO
}

DIBBS_ENHANCED = {
    "id": 2, 
    "is_default": False,
    "label": "DIBBs Enhanced algorithm",
    "description": "DIBBs Enhanced algorithm description"   #TODO
}

DIBBS_BASIC_PASS_ONE = {
    "id": 1,
    "algorithm_id": 1,
    "blocking_keys": [BlockingKey.BIRTHDATE, BlockingKey.MRN, BlockingKey.SEX],
    "evaluators": [{"first_name": "func:recordlinker.linkage.matchers.feature_match_fuzzy_string", "last_name": "func:recordlinker.linkage.matchers.feature_match_exact"}],
    "rule": "func:recordlinker.linkage.matchers.eval_perfect_match",
    "cluster_ratio": 0.9,
    "kwargs": {"thresholds": FUZZY_THRESHOLDS}
}

DIBBS_BASIC_PASS_TWO = {
    "id": 2,
    "algorithm_id": 1,
    "blocking_keys": [BlockingKey.ZIP, BlockingKey.FIRST_NAME, BlockingKey.LAST_NAME, BlockingKey.SEX],
    "evaluators": [{"address": "func:recordlinker.linkage.matchers.feature_match_fuzzy_string", "birthdate": "func:recordlinker.linkage.matchers.feature_match_exact"}],
    "rule": "func:recordlinker.linkage.matchers.eval_perfect_match",
    "cluster_ratio": 0.9,
    "kwargs": {"thresholds": FUZZY_THRESHOLDS}
}

DIBBS_ENHANCED_PASS_ONE = {
    "id": 3,
    "algorithm_id": 2,
    "blocking_keys": [BlockingKey.BIRTHDATE, BlockingKey.MRN, BlockingKey.SEX],
    "evaluators": [{"first_name": "func:recordlinker.linkage.matchers.feature_match_log_odds_fuzzy_compare", "last_name": "func:recordlinker.linkage.matchers.feature_match_log_odds_fuzzy_compare"}],
    "rule": "func:recordlinker.linkage.matchers.eval_log_odds_cutoff",
    "cluster_ratio": 0.9,
    "kwargs": {
            "similarity_measure": "JaroWinkler",
            "thresholds": FUZZY_THRESHOLDS,
            "true_match_threshold": 12.2,
            "log_odds": LOG_ODDS_SCORES,
        }
}

DIBBS_ENHANCED_PASS_TWO = {
    "id": 4,
    "algorithm_id": 2,
    "blocking_keys": [BlockingKey.ZIP, BlockingKey.FIRST_NAME, BlockingKey.LAST_NAME, BlockingKey.SEX],
    "evaluators": [{"address": "func:recordlinker.linkage.matchers.feature_match_log_odds_fuzzy_compare", "birthdate": "func:recordlinker.linkage.matchers.feature_match_log_odds_fuzzy_compare"}],
    "rule": "func:recordlinker.linkage.matchers.eval_log_odds_cutoff",
    "cluster_ratio": 0.9,
    "kwargs": {
            "similarity_measure": "JaroWinkler",
            "thresholds": FUZZY_THRESHOLDS,
            "true_match_threshold": 17.0,
            "log_odds": LOG_ODDS_SCORES,
        }
}

def upgrade() -> None:
    #insert alogithms
    sa.insert(Algorithm).values(DIBBS_BASIC)
    sa.insert(Algorithm).values(DIBBS_ENHANCED)
    
    #insert algorithm passes
    sa.insert(AlgorithmPass).values(DIBBS_BASIC_PASS_ONE)
    sa.insert(AlgorithmPass).values(DIBBS_BASIC_PASS_TWO)
    sa.insert(AlgorithmPass).values(DIBBS_ENHANCED_PASS_ONE)
    sa.insert(AlgorithmPass).values(DIBBS_ENHANCED_PASS_TWO)

def downgrade() -> None:
    #delete algorithm rows
    sa.delete(Algorithm).where(Algorithm.id == 1)
    sa.delete(Algorithm).where(Algorithm.id == 2)

    #delete algorithm pass rows
    sa.delete(AlgorithmPass).where(AlgorithmPass.id == 1)
    sa.delete(AlgorithmPass).where(AlgorithmPass.id == 2)
    sa.delete(AlgorithmPass).where(AlgorithmPass.id == 3)
    sa.delete(AlgorithmPass).where(AlgorithmPass.id == 4)
