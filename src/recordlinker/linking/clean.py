"""
recordlinker.linking.clean
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module is used to clean the data before running the linkage algorithm
"""

import fnmatch

from recordlinker import schemas
from recordlinker.schemas.algorithm import SkipValue
from recordlinker.schemas.identifier import IdentifierType


def _matches(value: str, values: list[str]) -> bool:
    ""
    for v in values:
        if fnmatch.fnmatch(value, v):
            return True
    return False


def clean(record: schemas.PIIRecord, skips: list[SkipValue]) -> schemas.PIIRecord:
    ""
    cleaned: schemas.PIIRecord = record.model_copy(deep=True)
    for skip in skips:
        values: list[str] = skip.values
        feat_attr: schemas.FeatureAttribute | None = None
        feat_suff: IdentifierType | None = None
        if skip.feature != "*":
            feat = schemas.Feature.parse(skip.feature)
            feat_attr = feat.attribute
            feat_suff = feat.suffix

        if feat_attr in (schemas.FeatureAttribute.BIRTHDATE, None):
            if record.birth_date and _matches(str(record.birth_date), values):
                cleaned.birth_date = None
        elif feat_attr in (schemas.FeatureAttribute.SEX, None):
            if record.sex and _matches(str(record.sex), values):
                cleaned.sex = None
        elif feat_attr in (schemas.FeatureAttribute.ADDRESS, None):
            for idx, address in enumerate(record.address):
                if address.line and _matches(address.line[0], values):
                    cleaned.address[idx].line[0] = ""
        elif feat_attr in (schemas.FeatureAttribute.CITY, None):
            for idx, address in enumerate(record.address):
                if address.city and _matches(address.city, values):
                    cleaned.address[idx].city = None
        elif feat_attr in (schemas.FeatureAttribute.STATE, None):
            for idx, address in enumerate(record.address):
                if address.state and _matches(address.state, values):
                    cleaned.address[idx].state = None
        elif feat_attr in (schemas.FeatureAttribute.ZIP, None):
            for idx, address in enumerate(record.address):
                if address.postal_code and _matches(address.postal_code, values):
                    cleaned.address[idx].postal_code = None
        elif feat_attr in (schemas.FeatureAttribute.GIVEN_NAME, None):
            for n_idx, name in enumerate(record.name):
                for g_idx, given in enumerate(name.given):
                    if given and _matches(given, values):
                        cleaned.name[n_idx].given[g_idx] = ""
        elif feat_attr in (schemas.FeatureAttribute.FIRST_NAME, None):
            for idx, name in enumerate(record.name):
                if name.given and _matches(name.given[0], values):
                    cleaned.name[idx].given[0] = ""
        elif feat_attr in (schemas.FeatureAttribute.LAST_NAME, None):
            for idx, name in enumerate(record.name):
                if name.family and _matches(name.family, values):
                    cleaned.name[idx].family = ""
        elif feat_attr in (schemas.FeatureAttribute.RACE, None):
            for idx, race in enumerate(record.race):
                if race and _matches(str(race), values):
                    cleaned.race[idx] = None
        elif feat_attr in (schemas.FeatureAttribute.TELECOM, None):
            for idx, telecom in enumerate(record.telecom):
                if telecom.value and _matches(telecom.value, values):
                    cleaned.telecom[idx].value = ""
        elif feat_attr in (schemas.FeatureAttribute.PHONE, None):
            for idx, telecom in enumerate(record.telecom):
                if telecom.value and telecom.system == "phone" and _matches(telecom.value, values):
                    cleaned.telecom[idx].value = ""
        elif feat_attr in (schemas.FeatureAttribute.EMAIL, None):
            for idx, telecom in enumerate(record.telecom):
                if telecom.value and telecom.system == "email" and _matches(telecom.value, values):
                    cleaned.telecom[idx].value = ""
        elif feat_attr in (schemas.FeatureAttribute.SUFFIX, None):
            for r_idx, name in enumerate(record.name):
                for s_idx, suffix in enumerate(name.suffix):
                    if suffix and _matches(suffix, values):
                        cleaned.name[r_idx].suffix[s_idx] = ""
        elif feat_attr in (schemas.FeatureAttribute.COUNTY, None):
            for idx, address in enumerate(record.address):
                if address.county and _matches(address.county, values):
                    cleaned.address[idx].county = None
        elif feat_attr in (schemas.FeatureAttribute.IDENTIFIER, None):
            for idx, ident in enumerate(record.identifiers):
                if feat_suff is None or feat_suff == ident.type:
                    parts: list[str | None] = [ident.value, ident.authority, str(ident.type)]
                    val = ":".join([p for p in parts if p])
                    if _matches(val, values):
                        cleaned.identifiers[idx].value = None
    return cleaned
