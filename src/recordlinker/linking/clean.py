"""
recordlinker.linking.clean
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module is used to clean the data before running the linkage algorithm
"""

import fnmatch

from recordlinker import schemas
from recordlinker.schemas.algorithm import SkipValue
from recordlinker.schemas.identifier import IdentifierType


def _match_skip_values(value: str, values: list[str]) -> bool:
    """
    Return whether the value matches any of the values in the list
    using case-insensitive fnmatch matching.

    :param value: the value to match
    :param values: the list of values to match
    :return: True if the value matches any of the values in the list
    """
    val = value.lower()
    return any(fnmatch.fnmatch(val, v.lower()) for v in values)


def remove_skip_values(record: schemas.PIIRecord, skips: list[SkipValue]) -> schemas.PIIRecord:
    """
    Return a copy of the incoming record, cleaned of any values identified in the
    skip list.

    :param record: the record to clean
    :param skips: the list of values to skip
    :return: a cleaned copy of the incoming record
    """
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
            if record.birth_date and _match_skip_values(str(record.birth_date), values):
                cleaned.birth_date = None
        if feat_attr in (schemas.FeatureAttribute.SEX, None):
            if record.sex and _match_skip_values(str(record.sex), values):
                cleaned.sex = None
        if feat_attr in (schemas.FeatureAttribute.ADDRESS, None):
            for idx, address in enumerate(record.address):
                if address.line and _match_skip_values(address.line[0], values):
                    cleaned.address[idx].line[0] = ""
        if feat_attr in (schemas.FeatureAttribute.CITY, None):
            for idx, address in enumerate(record.address):
                if address.city and _match_skip_values(address.city, values):
                    cleaned.address[idx].city = ""
        if feat_attr in (schemas.FeatureAttribute.STATE, None):
            for idx, address in enumerate(record.address):
                if address.state and _match_skip_values(address.state, values):
                    cleaned.address[idx].state = ""
        if feat_attr in (schemas.FeatureAttribute.ZIP, None):
            for idx, address in enumerate(record.address):
                if address.postal_code and _match_skip_values(address.postal_code, values):
                    cleaned.address[idx].postal_code = ""
        if feat_attr in (schemas.FeatureAttribute.GIVEN_NAME, None):
            for n_idx, name in enumerate(record.name):
                for g_idx, given in enumerate(name.given):
                    if given and _match_skip_values(given, values):
                        cleaned.name[n_idx].given[g_idx] = ""
        if feat_attr in (schemas.FeatureAttribute.FIRST_NAME, None):
            for idx, name in enumerate(record.name):
                if name.given and _match_skip_values(name.given[0], values):
                    cleaned.name[idx].given[0] = ""
        if feat_attr in (schemas.FeatureAttribute.LAST_NAME, None):
            for idx, name in enumerate(record.name):
                if name.family and _match_skip_values(name.family, values):
                    cleaned.name[idx].family = ""
        if feat_attr in (schemas.FeatureAttribute.NAME, None):
            for idx, name in enumerate(record.name):
                nval = f"{' '.join(name.given)} {name.family}"
                if name and _match_skip_values(nval, values):
                    cleaned.name[idx].given = []
                    cleaned.name[idx].family = ""
        if feat_attr in (schemas.FeatureAttribute.RACE, None):
            for idx in reversed(range(len(record.race))):
                # We are iterating through the list backwards so we can safely delete
                # elements from the cleaned list without causing an index error
                race = record.race[idx]
                if race and _match_skip_values(str(race), values):
                    del cleaned.race[idx]
        if feat_attr in (schemas.FeatureAttribute.TELECOM, None):
            for idx, telecom in enumerate(record.telecom):
                if telecom.value and _match_skip_values(telecom.value, values):
                    cleaned.telecom[idx].value = ""
        if feat_attr in (schemas.FeatureAttribute.PHONE, None):
            for idx, telecom in enumerate(record.telecom):
                if (
                    telecom.value
                    and telecom.system == "phone"
                    and _match_skip_values(telecom.value, values)
                ):
                    cleaned.telecom[idx].value = ""
        if feat_attr in (schemas.FeatureAttribute.EMAIL, None):
            for idx, telecom in enumerate(record.telecom):
                if (
                    telecom.value
                    and telecom.system == "email"
                    and _match_skip_values(telecom.value, values)
                ):
                    cleaned.telecom[idx].value = ""
        if feat_attr in (schemas.FeatureAttribute.SUFFIX, None):
            for r_idx, name in enumerate(record.name):
                for s_idx, suffix in enumerate(name.suffix):
                    if suffix and _match_skip_values(suffix, values):
                        cleaned.name[r_idx].suffix[s_idx] = ""
        if feat_attr in (schemas.FeatureAttribute.COUNTY, None):
            for idx, address in enumerate(record.address):
                if address.county and _match_skip_values(address.county, values):
                    cleaned.address[idx].county = ""
        if feat_attr in (schemas.FeatureAttribute.IDENTIFIER, None):
            for idx, ident in enumerate(record.identifiers):
                if feat_suff is None or feat_suff == ident.type:
                    val = f"{ident.value}:{ident.authority or ''}:{ident.type}"
                    if _match_skip_values(val, values):
                        cleaned.identifiers[idx].value = ""
    return cleaned
