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
from recordlinker.utils.normalize import normalize_text

# Load the state code mapping for state normalization in Address class
_STATE_NAME_TO_CODE = utils.read_json("assets/states.json")
_STATE_CODE_TO_NAME = {v: k for k, v in _STATE_NAME_TO_CODE.items()}

# Load suffix mappings for Name normalization
_SUFFIX_VARIANTS_TO_STANDARD_SUFFIXES = utils.read_json("assets/suffixes.json")
_PROCESSED_SUFFIXES = set(_SUFFIX_VARIANTS_TO_STANDARD_SUFFIXES.values())


class FeatureAttribute(enum.Enum):
    """
    Enum for the different Patient attributes that can be used for comparison.
    """

    BIRTHDATE = "BIRTHDATE"
    SEX = "SEX"
    GIVEN_NAME = "GIVEN_NAME"
    FIRST_NAME = "FIRST_NAME"
    LAST_NAME = "LAST_NAME"
    NAME = "NAME"
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
    def strip_whitespace(cls, v: typing.Any) -> str:
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

    @pydantic.model_serializer()
    def __str__(self):
        """
        Override the default model dump to create a single string for Feature.
        """
        if self.suffix:
            return f"{self.attribute}:{self.suffix}"
        return str(self.attribute)

    def values_to_match(self) -> typing.Iterator[str]:
        """
        Return an iterator of all possible values for this feature that can be used for comparison.
        """
        yield str(self)
        if self.suffix:
            yield str(self.attribute)

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

    @pydantic.field_validator("suffix", mode="before")
    def parse_suffix(cls, value: list[str]) -> list[str]:
        """
        Parse and normalize the suffix field into a standard representation.
        """
        normalized: list[str] = []
        if value:
            for sfx in value:
                suffix = str(sfx).title()
                if suffix in _SUFFIX_VARIANTS_TO_STANDARD_SUFFIXES:
                    suffix = _SUFFIX_VARIANTS_TO_STANDARD_SUFFIXES[suffix]
                # If the parsed suffix isn't one of our permitted output values at
                # this point, the user gave us something we don't handle, so revert
                # back to the raw value
                if suffix not in _PROCESSED_SUFFIXES:
                    suffix = str(sfx)
                normalized.append(suffix)
            return normalized
        return value


class Address(StrippedBaseModel):
    """
    The schema for an address record.
    """

    ST_SUFFIXES: typing.ClassVar[dict[str, str]] = utils.read_json(
        "assets/usps_street_suffixes.json"
    )
    model_config = pydantic.ConfigDict(extra="allow")

    line: typing.List[str] = pydantic.Field(
        default_factory=list,
        description=(
            "A list of street name, number, direction & P.O. Box etc., "
            "the order in which lines should appear in an address label."
        ),
    )
    city: typing.Optional[str] = pydantic.Field(default=None, description="Name of city, town etc.")
    state: typing.Optional[str] = pydantic.Field(
        default=None, description="US State or abbreviation"
    )
    postal_code: typing.Optional[str] = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices(
            "postal_code", "postalcode", "postalCode", "zip_code", "zipcode", "zipCode", "zip"
        ),
        description="Postal code for area",
    )
    county: typing.Optional[str] = pydantic.Field(default=None, description="Name of county")
    country: typing.Optional[str] = pydantic.Field(default=None, description="Name of country")
    latitude: typing.Optional[float] = pydantic.Field(
        default=None, description="Latitude of address"
    )
    longitude: typing.Optional[float] = pydantic.Field(
        default=None, description="Longitude of address"
    )

    @pydantic.field_validator("line", mode="before")
    def parse_line(cls, value: list[str]) -> list[str]:
        """
        Parse the line field into a list of strings with normalized street suffixes.
        """
        normalized: list[str] = []
        if value:
            for line in value:
                if line is not None:
                    parts = line.strip().split(" ")
                    # remove all non-alphanumeric characters and convert to uppercase
                    suffix = "".join(c for c in parts[-1] if c.isalnum()).upper()
                    if common := cls.ST_SUFFIXES.get(suffix):
                        # replace the suffix with the common suffix
                        parts[-1] = common
                    normalized.append(" ".join(parts))
        return normalized

    @pydantic.field_validator("state", mode="before")
    def parse_state(cls, value: str) -> str | None:
        """
        Normalize the state field into 2-letter USPS code.
        """
        if value:
            state = value.strip().title()
            # reduce inner whitespace to a single whitespace char
            state = " ".join(w for w in state.split(" ") if w)

            if len(state) == 2 and state.upper() in _STATE_CODE_TO_NAME:
                return state.upper()

            if state in _STATE_NAME_TO_CODE:
                return _STATE_NAME_TO_CODE[state]
        return value


class Telecom(StrippedBaseModel):
    """
    The schema for a telecom record.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    value: str
    system: typing.Optional[str] = None
    use: typing.Optional[str] = None

    @pydantic.model_validator(mode="after")
    def validate_and_normalize_telecom(self) -> typing.Self:
        """
        Validate and normalize the telecom record.
        """
        # If telecom.system = "email", set telecom.value to lowercase
        #
        if self.system == "email":
            self.value = self.value.strip().lower()
        # If telecom.system = "phone", normalize the number
        elif self.system == "phone":
            try:
                # Attempt to parse with country code
                if self.value.startswith("+"):
                    parsed_number = phonenumbers.parse(self.value)
                else:
                    # Default to US if no country code is provided
                    parsed_number = phonenumbers.parse(self.value, "US")
                self.value = str(parsed_number.national_number)
            except phonenumbers.NumberParseException:
                # If parsing fails, return the original phone number
                pass

        return self


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
    def from_patient(cls, patient: models.Patient) -> "PIIRecord":
        """
        Construct a PIIRecord from a Patient model.
        """
        return PIIRecord.from_data(patient.data)

    @classmethod
    def from_data(cls, data: dict) -> typing.Self:
        """
        Construct a PIIRecord from an extracted data dictionary of a
        Patient model.
        """
        obj = cls.model_construct(**data)
        obj.address = [Address.model_construct(**a) for a in data.get("address", [])]
        obj.name = [Name.model_construct(**n) for n in data.get("name", [])]
        obj.telecom = [Telecom.model_construct(**t) for t in data.get("telecom", [])]
        obj.identifiers = [Identifier.model_construct(**i) for i in data.get("identifiers", [])]
        return obj

    def to_data(self) -> dict[str, typing.Any]:
        """
        Convert this PIIRecord into a data dict.
        """
        return self.to_dict(prune_empty=True)

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
        if not value:
            return []
        return [Race.parse(v) for v in value if v is not None]

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

    def feature_iter(self, feature: Feature, prepend_suffix: bool = False) -> typing.Iterator[str]:
        """
        Given a field name, return an iterator of all string values for that field.
        Empty strings are not included in the iterator. Includes an optional
        parameter that can be used when invoking `feature_iter` on the FIRST_NAME
        field; if this parameter is true, the value yielded is the concatenation
        `SUFFIX + FIRST_NAME`.

        :param prepend_suffix: An optional boolean indicating whether a suffix
          should be prepended to a first name for blocking purposes. Has no
          effect for features other than FIRST_NAME.
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
                    yield address.state
        elif attribute == FeatureAttribute.ZIP:
            for address in self.address:
                if address.postal_code:
                    # FIXME: should we normalize zip codes during ingest, rather than here?
                    # only use the first 5 digits for comparison
                    yield address.postal_code[:5]
        elif attribute == FeatureAttribute.GIVEN_NAME:
            for name in self.name:
                if name.given:
                    yield normalize_text("".join(name.given))
        elif attribute == FeatureAttribute.FIRST_NAME:
            for name in self.name:
                # We only want the first suffix, and only if it's valid
                # (i.e. an accepted output of normalization)
                suffix: str = (name.suffix or [""])[0]
                if suffix not in _PROCESSED_SUFFIXES:
                    suffix = ""
                # We only care about the first given name for comparisons
                for given in name.given[0:1]:
                    if given:
                        if prepend_suffix:
                            yield normalize_text(suffix + given)
                        else:
                            yield normalize_text(given)
        elif attribute == FeatureAttribute.LAST_NAME:
            for name in self.name:
                if name.family:
                    yield normalize_text(name.family)
        elif attribute == FeatureAttribute.NAME:
            for name in self.name:
                yield normalize_text("".join(name.given[0:1] + [name.family]))
        elif attribute == FeatureAttribute.RACE:
            for race in self.race:
                if race and race not in [Race.UNKNOWN, Race.ASKED_UNKNOWN]:
                    yield str(race)
        elif attribute == FeatureAttribute.TELECOM:
            for telecom in self.telecom:
                if telecom.system == "phone":
                    yield normalize_text(telecom.value)
                else:
                    yield telecom.value
        elif attribute == FeatureAttribute.PHONE:
            for telecom in self.telecom:
                if telecom.system == "phone":
                    yield normalize_text(telecom.value)
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
                {
                    x[:4]
                    for x in self.feature_iter(
                        Feature(attribute=FeatureAttribute.FIRST_NAME), prepend_suffix=True
                    )
                }
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


class TuningPair(pydantic.BaseModel):
    """
    A pair of PIIRecords that are used for training a model.
    """

    record1: PIIRecord
    record2: PIIRecord
    sample_used: typing.Optional[int] = None

    @classmethod
    def from_data(cls, record1: dict, record2: dict, sample_used: int | None = None) -> typing.Self:
        """
        Contruct a TuningPair from raw PII data dictionaries.
        """
        return cls.model_construct(
            record1=PIIRecord.from_data(record1),
            record2=PIIRecord.from_data(record2),
            sample_used=sample_used,
        )
