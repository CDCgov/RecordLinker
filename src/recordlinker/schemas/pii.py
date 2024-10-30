import datetime
import enum
import re
import typing

import dateutil.parser
import pydantic

from recordlinker import models


class Feature(enum.Enum):
    """
    Enum for the different Patient attributes that can be used for comparison.
    """

    BIRTHDATE = "BIRTHDATE"
    MRN = "MRN"
    SEX = "SEX"
    FIRST_NAME = "FIRST_NAME"
    LAST_NAME = "LAST_NAME"
    ADDRESS = "ADDRESS"
    CITY = "CITY"
    STATE = "STATE"
    ZIP = "ZIP"
    SSN = "SSN"
    RACE = "RACE"
    GENDER = "GENDER"
    TELEPHONE = "TELEPHONE"
    SUFFIX = "SUFFIX"
    COUNTY = "COUNTY"

    def __str__(self):
        """
        Return the value of the enum as a string.
        """
        return self.value


class Sex(enum.Enum):
    """
    Enum for the Patient.sex field.
    """

    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"

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
    
class Gender(enum.Enum):
    """
    Enum for the Gender field.
    """

    FEMALE = "FEMALE"
    MALE = "MALE"
    NON_BINARY = "NON_BINARY"
    ASKED_DECLINED = "ASKED_DECLINED"
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

    value: str  # future use
    system: typing.Optional[str] = None
    use: typing.Optional[str] = None


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
    mrn: typing.Optional[str] = None
    address: typing.List[Address] = []
    name: typing.List[Name] = []
    telecom: typing.List[Telecom] = []
    ssn: typing.Optional[str] = None
    race: typing.Optional[Race] = None
    gender: typing.Optional[Gender] = None

    @classmethod
    def model_construct(cls, _fields_set: set[str] | None = None, **values: typing.Any) -> typing.Self:
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
            return Sex.UNKNOWN
    
    @pydantic.field_validator("ssn", mode="before")
    def parse_ssn(cls, value):
        """
        Parse the ssn string 
        """
        if value:
            val = str(value).strip()
            
            if re.match(r"^\d{3}-\d{2}-\d{4}$", val):
                return val 

            if len(val) != 9 or not val.isdigit():
                return None
            
            # Format back to the standard SSN format (XXX-XX-XXXX)
            formatted_ssn = f"{val[:3]}-{val[3:5]}-{val[5:]}"
            return formatted_ssn
    
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

                
            
    @pydantic.field_validator("gender", mode="before")
    def parse_gender(cls, value):
        """
        Prase the gender string into a gender enum
        """
        if value:
            val = str(value).lower().strip()
            try:
                return Gender(val)
            except ValueError:
                if "female" in val:
                    return Gender.FEMALE
                elif "male" in val:
                    return Gender.MALE
                elif "nonbinary" in val:
                    return Gender.NON_BINARY
                elif "declined" in val or "asked" in val:
                    return Gender.ASKED_DECLINED
                return Gender.UNKNOWN

    def feature_iter(self, feature: Feature) -> typing.Iterator[str]:
        """
        Given a field name, return an iterator of all string values for that field.
        Empty strings are not included in the iterator.
        """
        if not isinstance(feature, Feature):
            raise ValueError(f"Invalid feature: {feature}")

        if feature == Feature.BIRTHDATE:
            if self.birth_date:
                yield str(self.birth_date)
        elif feature == Feature.MRN:
            if self.mrn:
                yield self.mrn
        elif feature == Feature.SEX:
            if self.sex:
                yield str(self.sex)
        elif feature == Feature.ADDRESS:
            for address in self.address:
                # The 2nd, 3rd, etc lines of an address are not as important as
                # the first line, so we only include the first line in the comparison.
                if address.line and address.line[0]:
                    yield address.line[0]
        elif feature == Feature.CITY:
            for address in self.address:
                if address.city:
                    yield address.city
        elif feature == Feature.STATE:
            for address in self.address:
                if address.state:
                    yield address.state
        elif feature == Feature.ZIP:
            for address in self.address:
                if address.postal_code:
                    # only use the first 5 digits for comparison
                    yield address.postal_code[:5]
        elif feature == Feature.FIRST_NAME:
            for name in self.name:
                for given in name.given:
                    if given:
                        yield given
        elif feature == Feature.LAST_NAME:
            for name in self.name:
                if name.family:
                    yield name.family
        elif feature == Feature.SSN:
            if self.ssn:
                yield self.ssn
        elif feature == Feature.RACE:
            if self.race:
                yield str(self.race)
        elif feature == Feature.GENDER:
            if self.gender:
                yield str(self.gender)
        elif feature == Feature.TELEPHONE:
            for telecom in self.telecom:
                if telecom.value:
                    yield telecom.value
        elif feature == Feature.SUFFIX:
            for name in self.name:
                for suffix in name.suffix:
                    if suffix:
                        yield suffix
        elif feature == Feature.COUNTY:
            for address in self.address:
                if address.county:
                    yield address.county

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
            vals.update(self.feature_iter(Feature.BIRTHDATE))
        elif key == models.BlockingKey.MRN:
            vals.update({x[-4:] for x in self.feature_iter(Feature.MRN)})
        elif key == models.BlockingKey.SEX:
            vals.update(self.feature_iter(Feature.SEX))
        elif key == models.BlockingKey.ZIP:
            vals.update(self.feature_iter(Feature.ZIP))
        elif key == models.BlockingKey.FIRST_NAME:
            vals.update({x[:4] for x in self.feature_iter(Feature.FIRST_NAME)})
        elif key == models.BlockingKey.LAST_NAME:
            vals.update({x[:4] for x in self.feature_iter(Feature.LAST_NAME)})
        elif key == models.BlockingKey.ADDRESS:
            vals.update({x[:4] for x in self.feature_iter(Feature.ADDRESS)})

        # if any vals are longer than the BLOCKING_KEY_MAX_LENGTH, raise an error
        if any(len(x) > models.BLOCKING_VALUE_MAX_LENGTH for x in vals):
            raise RuntimeError(f"{self} has a value longer than {models.BLOCKING_VALUE_MAX_LENGTH}")
        return vals
