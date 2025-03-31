import datetime
import enum
import functools
import json
import typing

import phonenumbers
import pydantic
from dateutil.parser import parse
from dateutil.parser import parserinfo

from recordlinker import models
from recordlinker.schemas.identifier import Identifier
from recordlinker.schemas.identifier import IdentifierType
from recordlinker.utils import path as utils
from recordlinker.utils.normalize import normalize_phone_number
from recordlinker.utils.normalize import normalize_text

# Load the state code mapping for state normalization in Address class
_STATE_NAME_TO_CODE = utils.read_json("assets/states.json")
_STATE_CODE_TO_NAME = {v: k for k, v in _STATE_NAME_TO_CODE.items()}


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


class StrippedBaseModel(pydantic.BaseModel):
    @pydantic.field_validator("*", mode="before")
    def strip_whitespace(cls, v):
        """
        Remove leading and trailing whitespace from all string fields.
        """
        if isinstance(v, str):
            return v.strip()
        return v


class Feature(StrippedBaseModel):
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

    @classmethod
    @functools.cache
    def parse(cls, value: str) -> "Race":
        """
        Parse a race string into a Race enum.
        """
        # Create a list of string/race mappings, this is intentionally ordered
        # to ensure we test for the substrings in the correct order
        mapping = [
            (["american indian", "alaska native"], cls.AMERICAN_INDIAN),
            (["asian"], cls.ASIAN),
            (["black", "african american"], cls.BLACK),
            (["white"], cls.WHITE),
            (["hawaiian", "pacific islander"], cls.HAWAIIAN),
            (["asked unknown", "asked but unknown"], cls.ASKED_UNKNOWN),
            (["unknown"], cls.UNKNOWN),
        ]
        val = value.lower().strip()
        for substrings, race in mapping:
            if any(substring in val for substring in substrings):
                return race
        return cls.OTHER

    def __str__(self):
        """
        Return the value of the enum as a string.
        """
        return self.value


class Name(StrippedBaseModel):
    """
    The schema for a name record.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    family: str
    given: typing.List[str] = []
    use: typing.Optional[str] = None
    prefix: typing.List[str] = []  # future use
    suffix: typing.List[str] = []


class Address(StrippedBaseModel):
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

    @functools.cached_property
    def normalize_state(self) -> str | None:
        """
        Normalize the state field into 2-letter USPS code.
        """

        if self.state:
            state = self.state.strip().title()

            if len(state) == 2 and state.upper() in _STATE_CODE_TO_NAME:
                return self.state.upper()

            if state in _STATE_NAME_TO_CODE:
                return _STATE_NAME_TO_CODE[state]

        return None


class Telecom(StrippedBaseModel):
    """
    The schema for a telecom record.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    value: str
    system: typing.Optional[str] = None
    use: typing.Optional[str] = None

    @pydantic.model_validator(mode="before")
    def validate_and_normalize_telecom(cls, values):
        """
        Validate and normalize the telecom record.
        """
        # If telecom.system = "email", set telecom.value to lowercase
        if values.get("system") == "email":
            values["value"] = values["value"].strip()
        # If telecom.system = "phone", normalize the number
        elif values.get("system") == "phone":
            values["value"] = normalize_phone_number(values["value"])

        return values


class PIIRecord(StrippedBaseModel):
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
    race: typing.List[Race] = []
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

        class LinkerParserInfo(parserinfo):
            def convertyear(self, year, *args):
                """
                Subclass method override for parser info function dedicated to
                handling two-digit year strings. The Parser interprets any two
                digit year string up to and including the last two digits of
                the current year as the current century; any two-digit value
                above this number is interpreted as the preceding century.
                E.g. '25' is parsed to '2025', but '74' becomes '1974'.
                The Parser does not accept dates in the future, even if in
                the same calendar year.
                """
                # self._year is the current four-digit year
                # self._century is self._year with the tens and ones digits dropped, e.g.
                # 19XX becomes 1900, 20XX becomes 2000
                # implementation override follows template pattern in docs
                # https://dateutil.readthedocs.io/en/latest/_modules/dateutil/parser/_parser.html#parserinfo.convertyear # noqa: E712
                if year < 100:
                    year += self._century
                    if year > self._year:
                        # This allows us to continually make a pivot at the current year;
                        # Keeps with best practice and conventional norms
                        year -= 100
                return year

        if value:
            given_date = parse(str(value), LinkerParserInfo())
            if given_date > datetime.datetime.today():
                raise ValueError("Birthdates cannot be in the future")
            if given_date < datetime.datetime(1850, 1, 1):
                raise ValueError("Birthdates cannot be before 1850")
            return given_date

    @pydantic.field_validator("sex", mode="before")
    def parse_sex(cls, value):
        """
        Parse the sex value into a sex enum.
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
        Parse the race string into a race enum.
        """
        return [Race.parse(v) for v in value]

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
                    yield normalize_text(address.line[0])
        elif attribute == FeatureAttribute.CITY:
            for address in self.address:
                if address.city:
                    yield normalize_text(address.city)
        elif attribute == FeatureAttribute.STATE:
            for address in self.address:
                if address.state:
                    state = address.normalize_state
                    if state:
                        yield state
        elif attribute == FeatureAttribute.ZIP:
            for address in self.address:
                if address.postal_code:
                    # only use the first 5 digits for comparison
                    yield address.postal_code[:5]
        elif attribute == FeatureAttribute.GIVEN_NAME:
            for name in self.name:
                if name.given:
                    yield normalize_text("".join(name.given))
        elif attribute == FeatureAttribute.FIRST_NAME:
            for name in self.name:
                # We only want the first given name for comparison
                for given in name.given[0:1]:
                    if given:
                        yield normalize_text(given)
        elif attribute == FeatureAttribute.LAST_NAME:
            for name in self.name:
                if name.family:
                    yield normalize_text(name.family)
        elif attribute == FeatureAttribute.RACE:
            for race in self.race:
                if race and race not in [Race.UNKNOWN, Race.ASKED_UNKNOWN]:
                    yield str(race)
        elif attribute == FeatureAttribute.TELECOM:
            for telecom in self.telecom:
                value = telecom.value.strip()
                if telecom.system is None:
                    yield value
                    continue
                elif telecom.system == "email":
                    yield value
                elif telecom.system == "phone":
                    phone = str(phonenumbers.parse(telecom.value).national_number)
                    yield normalize_text(phone)
                # If the telecom system is not email or phone, just return the value
                else:
                    yield value
        elif attribute == FeatureAttribute.PHONE:
            for telecom in self.telecom:
                if telecom.system == "phone":
                    # Remove country code and extension from the phone number
                    parsed_phone = phonenumbers.parse(telecom.value)
                    phone = normalize_text(str(parsed_phone.national_number))
                    if phone:
                        yield phone
        elif attribute == FeatureAttribute.EMAIL:
            for telecom in self.telecom:
                if telecom.system == "email":
                    yield telecom.value
        elif attribute == FeatureAttribute.SUFFIX:
            for name in self.name:
                for suffix in name.suffix:
                    if suffix:
                        yield normalize_text(suffix)
        elif attribute == FeatureAttribute.COUNTY:
            for address in self.address:
                if address.county:
                    yield normalize_text(address.county)
        elif attribute == FeatureAttribute.IDENTIFIER:
            for identifier in self.identifiers:
                if identifier_suffix is None or identifier_suffix == identifier.type:
                    identifier_authority = identifier.authority or ""
                    yield f"{normalize_text(identifier.value)}:{normalize_text(identifier_authority) if identifier_authority else identifier_authority}:{identifier.type}"

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
