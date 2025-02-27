import datetime
import enum
import json
import re
import typing

import dateutil.parser
import pydantic

from recordlinker import models
from recordlinker.schemas.identifier import Identifier
from recordlinker.schemas.identifier import IdentifierType


class FeatureAttribute(enum.Enum):
    """
    Enum for the different Patient attributes that can be used for comparison.
    """

    BIRTHDATE = "BIRTHDATE"
    SEX = "SEX"
    GIVEN_NAME = "GIVEN_NAME"
    FIRST_NAME = "FIRST_NAME"
    LAST_NAME = "LAST_NAME"
    ADDRESS = "ADDRESS"
    CITY = "CITY"
    STATE = "STATE"
    ZIP = "ZIP"
    # GENDER removed to be in compliance with Executive Order 14168
    RACE = "RACE"
    TELECOM = "TELECOM"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    SUFFIX = "SUFFIX"
    COUNTY = "COUNTY"
    IDENTIFIER = "IDENTIFIER"

    def __str__(self):
        """
        Return the value of the enum as a string.
        """
        return self.value


class Feature(pydantic.BaseModel):
    """
    The schema for a feature.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    suffix: typing.Optional[IdentifierType] = None
    attribute: FeatureAttribute

    @classmethod
    def parse(cls, feature_string: str) -> typing.Self:
        """
        Parse a feature string in the format 'FEATURE_ATTRIBUTE:SUFFIX' into a Feature object.

        Args:
            feature_string (str): The string to parse.

        Returns:
            Feature: A Feature object with attribute and suffix populated.
        """
        # Split the feature string on ":"
        parts = feature_string.split(":", 1)
        feature_attribute = FeatureAttribute(parts[0])

        if len(parts) == 1:
            return cls(attribute=feature_attribute)

        # If suffix is provided, ensure the attribute is IDENTIFIER and validate the suffix
        if feature_attribute != FeatureAttribute.IDENTIFIER:
            raise ValueError(f"Suffix is not allowed for attribute '{feature_attribute}'")

        feature_suffix = IdentifierType(parts[1])
        return cls(attribute=feature_attribute, suffix=feature_suffix)

    @classmethod
    def all_options(cls) -> list[typing.Any]:
        """
        Return a list of all possible Feature string values that can be used for comparison.
        """
        options = []
        for feature in FeatureAttribute:
            options.append(str(feature))
            if feature == FeatureAttribute.IDENTIFIER:
                for identifier in IdentifierType:
                    options.append(f"{feature}:{identifier}")
        return options


class Sex(enum.Enum):
    """
    Enum for the Patient.sex field.
    """

    MALE = "M"
    FEMALE = "F"
    # UNKNOWN Sex removed to be in compliance with Executive Order 14168

    def __str__(self):
        """
        Return the value of the enum as a string.
        """
        return self.value


class Race(enum.Enum):
    """
    Enum for the Race field.
    """

    AMERICAN_INDIAN = "AMERICAN_INDIAN"
    ASIAN = "ASIAN"
    BLACK = "BLACK"
    HAWAIIAN = "HAWAIIAN"
    WHITE = "WHITE"
    OTHER = "OTHER"
    ASKED_UNKNOWN = "ASKED_UNKNOWN"
    UNKNOWN = "UNKNOWN"

    def __str__(self):
        """
        Return the value of the enum as a string.
        """
        return self.value


class Name(pydantic.BaseModel):
    """
    The schema for a name record.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    family: str
    given: typing.List[str] = []
    use: typing.Optional[str] = None
    prefix: typing.List[str] = []  # future use
    suffix: typing.List[str] = []


class Address(pydantic.BaseModel):
    """
    The schema for an address record.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    line: typing.List[str] = []
    city: typing.Optional[str] = None
    state: typing.Optional[str] = None
    postal_code: typing.Optional[str] = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices(
            "postal_code", "postalcode", "postalCode", "zip_code", "zipcode", "zipCode", "zip"
        ),
    )
    county: typing.Optional[str] = None
    country: typing.Optional[str] = None
    latitude: typing.Optional[float] = None
    longitude: typing.Optional[float] = None


class Telecom(pydantic.BaseModel):
    """
    The schema for a telecom record.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    value: str
    system: typing.Optional[str] = None
    use: typing.Optional[str] = None

    def phone_number(self) -> str | None:
        """
        Return the phone number from the telecom record.
        """
        if self.system != "phone":
            return None
        # normalize the number to include just the 10 digits
        return re.sub(r"\D", "", self.value)[:10]

    def email(self) -> str | None:
        """
        Return the email address from the telecom record.
        """
        if self.system != "email":
            return None
        return self.value


class PIIRecord(pydantic.BaseModel):
    """
    The schema for a PII record.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    external_id: typing.Optional[str] = None
    birth_date: typing.Optional[datetime.date] = pydantic.Field(
        default=None, validation_alias=pydantic.AliasChoices("birth_date", "birthdate", "birthDate")
    )
    sex: typing.Optional[Sex] = None
    address: typing.List[Address] = []
    name: typing.List[Name] = []
    telecom: typing.List[Telecom] = []
    race: typing.Optional[Race] = None
    identifiers: typing.List[Identifier] = []

    @classmethod
    def model_construct(
        cls, _fields_set: set[str] | None = None, **values: typing.Any
    ) -> typing.Self:
        """
        Construct a PIIRecord object from a dictionary. This is similar to the
        `pydantic.BaseModel.models_construct` method, but allows for additional parsing
        of nested objects.  The key difference between this and the __init__ constructor
        is this method will not parse and validate the data, thus should only be used
        when the data is already cleaned and validated.
        """
        obj = super(PIIRecord, cls).model_construct(_fields_set=_fields_set, **values)
        obj.address = [Address.model_construct(**a) for a in values.get("address", [])]
        obj.name = [Name.model_construct(**n) for n in values.get("name", [])]
        obj.telecom = [Telecom.model_construct(**t) for t in values.get("telecom", [])]
        obj.identifiers = [Identifier.model_construct(**i) for i in values.get("identifiers", [])]

        return obj

    @pydantic.field_validator("external_id", mode="before")
    def parse_external_id(cls, value):
        """
        Parse the external_id object into a string
        """
        if value:
            return str(value)

    @pydantic.field_validator("birth_date", mode="before")
    def parse_birth_date(cls, value):
        """
        Parse the birthdate string into a datetime object.
        """
        if value:
            return dateutil.parser.parse(str(value))

    @pydantic.field_validator("sex", mode="before")
    def parse_sex(cls, value):
        """
        Parse the
        """
        if value:
            val = str(value).lower().strip()
            if val in ["m", "male"]:
                return Sex.MALE
            elif val in ["f", "female"]:
                return Sex.FEMALE
            return None

    @pydantic.field_validator("race", mode="before")
    def parse_race(cls, value):
        """
        Prase the race string into a race enum
        """

        race_mapping = [
            (["american indian", "alaska native"], Race.AMERICAN_INDIAN),
            (["asian"], Race.ASIAN),
            (["black", "african american"], Race.BLACK),
            (["white"], Race.WHITE),
            (["hawaiian", "pacific islander"], Race.HAWAIIAN),
            (["asked unknown", "asked but unknown"], Race.ASKED_UNKNOWN),
            (["unknown"], Race.UNKNOWN),
        ]

        if value:
            val = str(value).lower().strip()
            for substrings, race in race_mapping:
                if any(substring in val for substring in substrings):
                    return race
            return Race.OTHER

    def to_json(self, prune_empty: bool = False) -> str:
        """
        Convert the PIIRecord object to a JSON string.
        """
        return self.model_dump_json(exclude_unset=prune_empty, exclude_none=prune_empty)

    def to_dict(self, prune_empty: bool = False) -> dict:
        """
        Convert the PIIRecord object to a dictionary.
        """
        # convert the data to a JSON string, then load it back as a dictionary
        # this is necessary to ensure all data elements are JSON serializable
        data = self.to_json(prune_empty=prune_empty)
        return json.loads(data)

    def feature_iter(self, feature: Feature) -> typing.Iterator[str]:
        """
        Given a field name, return an iterator of all string values for that field.
        Empty strings are not included in the iterator.
        """

        if not isinstance(feature, Feature):
            raise ValueError(f"Invalid feature: {feature}")

        attribute = feature.attribute
        identifier_suffix = feature.suffix

        if attribute == FeatureAttribute.BIRTHDATE:
            if self.birth_date:
                yield str(self.birth_date)
        elif attribute == FeatureAttribute.SEX:
            if self.sex:
                yield str(self.sex)
        elif attribute == FeatureAttribute.ADDRESS:
            for address in self.address:
                # The 2nd, 3rd, etc lines of an address are not as important as
                # the first line, so we only include the first line in the comparison.
                if address.line and address.line[0]:
                    yield address.line[0]
        elif attribute == FeatureAttribute.CITY:
            for address in self.address:
                if address.city:
                    yield address.city
        elif attribute == FeatureAttribute.STATE:
            for address in self.address:
                if address.state:
                    yield address.state
        elif attribute == FeatureAttribute.ZIP:
            for address in self.address:
                if address.postal_code:
                    # only use the first 5 digits for comparison
                    yield address.postal_code[:5]
        elif attribute == FeatureAttribute.GIVEN_NAME:
            for name in self.name:
                if name.given:
                    yield " ".join(name.given)
        elif attribute == FeatureAttribute.FIRST_NAME:
            for name in self.name:
                # We only want the first given name for comparison
                for given in name.given[0:1]:
                    if given:
                        yield given
        elif attribute == FeatureAttribute.LAST_NAME:
            for name in self.name:
                if name.family:
                    yield name.family
        elif attribute == FeatureAttribute.RACE:
            if self.race and self.race not in [Race.UNKNOWN, Race.ASKED_UNKNOWN]:
                yield str(self.race)
        elif attribute == FeatureAttribute.TELECOM:
            for telecom in self.telecom:
                if telecom.value:
                    yield telecom.value
        elif attribute == FeatureAttribute.PHONE:
            for telecom in self.telecom:
                number = telecom.phone_number()
                if number:
                    yield number
        elif attribute == FeatureAttribute.EMAIL:
            for telecom in self.telecom:
                email = telecom.email()
                if email:
                    yield email
        elif attribute == FeatureAttribute.SUFFIX:
            for name in self.name:
                for suffix in name.suffix:
                    if suffix:
                        yield suffix
        elif attribute == FeatureAttribute.COUNTY:
            for address in self.address:
                if address.county:
                    yield address.county
        elif attribute == FeatureAttribute.IDENTIFIER:
            for identifier in self.identifiers:
                if identifier_suffix is None or identifier_suffix == identifier.type:
                    yield f"{identifier.value}:{identifier.authority or ''}:{identifier.type}"

    def blocking_keys(self, key: models.BlockingKey) -> set[str]:
        """
        For a particular Feature, return a set of all possible Blocking Key values
        for this record.  Many keys will only have 1 possible value, but some (like
        first name) could have multiple values.
        """
        vals: set[str] = set()

        if not isinstance(key, models.BlockingKey):
            raise ValueError(f"Invalid BlockingKey: {key}")

        if key == models.BlockingKey.BIRTHDATE:
            # NOTE: we could optimize here and remove the dashes from the date
            vals.update(self.feature_iter(Feature(attribute=FeatureAttribute.BIRTHDATE)))
        elif key == models.BlockingKey.IDENTIFIER:
            for ident in self.feature_iter(Feature(attribute=FeatureAttribute.IDENTIFIER)):
                _value, _, _type = ident.split(":", 2)
                vals.add(f"{_value[-4:]}:{_type}")
        elif key == models.BlockingKey.SEX:
            vals.update(self.feature_iter(Feature(attribute=FeatureAttribute.SEX)))
        elif key == models.BlockingKey.ZIP:
            vals.update(self.feature_iter(Feature(attribute=FeatureAttribute.ZIP)))
        elif key == models.BlockingKey.FIRST_NAME:
            vals.update(
                {x[:4] for x in self.feature_iter(Feature(attribute=FeatureAttribute.FIRST_NAME))}
            )
        elif key == models.BlockingKey.LAST_NAME:
            vals.update(
                {x[:4] for x in self.feature_iter(Feature(attribute=FeatureAttribute.LAST_NAME))}
            )
        elif key == models.BlockingKey.ADDRESS:
            vals.update(
                {x[:4] for x in self.feature_iter(Feature(attribute=FeatureAttribute.ADDRESS))}
            )
        elif key == models.BlockingKey.PHONE:
            vals.update(
                {x[-4:] for x in self.feature_iter(Feature(attribute=FeatureAttribute.PHONE))}
            )
        elif key == models.BlockingKey.EMAIL:
            vals.update(
                {x[:4] for x in self.feature_iter(Feature(attribute=FeatureAttribute.EMAIL))}
            )

        # if any vals are longer than the BLOCKING_KEY_MAX_LENGTH, raise an error
        if any(len(x) > models.BLOCKING_VALUE_MAX_LENGTH for x in vals):
            raise RuntimeError(f"{self} has a value longer than {models.BLOCKING_VALUE_MAX_LENGTH}")
        return vals

    def blocking_values(self) -> typing.Iterator[tuple[models.BlockingKey, str]]:
        """
        Return an iterator of all possible BlockingValues for this record.
        """
        for key in models.BlockingKey:
            # For each Key, get all the values from the data dictionary
            # Many Keys will only have 1 value, but its possible that
            # a PII data dict could have multiple given names
            for val in self.blocking_keys(key):
                yield key, val
