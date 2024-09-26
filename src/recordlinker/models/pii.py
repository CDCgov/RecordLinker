import datetime
import enum
import typing

import dateutil.parser
import pydantic


class Feature(enum.Enum):
    """
    Enum for the different Patient attributes that can be used for comparison.
    """

    BIRTHDATE = "birthdate"
    MRN = "mrn"
    SEX = "sex"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    ZIPCODE = "zip"


class Sex(enum.Enum):
    """
    Enum for the Patient.sex field.
    """

    M = "MALE"
    F = "FEMALE"
    U = "UNKNOWN"


class Name(pydantic.BaseModel):
    """
    The schema for a name record.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    family: str
    given: typing.List[str] = []
    use: typing.Optional[str] = None
    prefix: typing.List[str] = []  # future use
    suffix: typing.List[str] = []  # future use


class Address(pydantic.BaseModel):
    """
    The schema for an address record.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    line: typing.List[str] = []
    city: typing.Optional[str] = None
    state: typing.Optional[str] = None
    postal_code: typing.Optional[str] = pydantic.Field(
        default=None, validation_alias=pydantic.AliasChoices("postal_code", "postalCode")
    )
    county: typing.Optional[str] = None  # future use
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
        default=None, validation_alias=pydantic.AliasChoices("birth_date", "birthDate")
    )
    sex: typing.Optional[Sex] = None
    mrn: typing.Optional[str] = None
    address: typing.List[Address] = []
    name: typing.List[Name] = []
    telecom: typing.List[Telecom] = []

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
                return Sex.M
            elif val in ["f", "female"]:
                return Sex.F
            return Sex.U

    def field_iter(self, field: Feature) -> typing.Iterator[str]:
        """
        Given a field name, return an iterator of all string values for that field.
        Empty strings are not included in the iterator.
        """
        if not isinstance(field, Feature):
            raise ValueError(f"Invalid feature: {field}")

        if field == Feature.BIRTHDATE:
            if self.birth_date:
                yield self.birth_date.strftime("%Y-%m-%d")
        elif field == Feature.MRN:
            if self.mrn:
                yield self.mrn
        elif field == Feature.SEX:
            if self.sex:
                yield self.sex.name.lower()
        elif field == Feature.ADDRESS:
            for address in self.address:
                for line in address.line:
                    if line:
                        yield line
        elif field == Feature.CITY:
            for address in self.address:
                if address.city:
                    yield address.city
        elif field == Feature.STATE:
            for address in self.address:
                if address.state:
                    yield address.state
        elif field == Feature.ZIPCODE:
            for address in self.address:
                if address.postal_code:
                    # only use the first 5 digits for comparison
                    yield address.postal_code[:5]
        elif field == Feature.FIRST_NAME:
            for name in self.name:
                for given in name.given:
                    if given:
                        yield given
        elif field == Feature.LAST_NAME:
            for name in self.name:
                if name.family:
                    yield name.family
