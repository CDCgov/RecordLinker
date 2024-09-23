import enum
import typing
import uuid

import dateutil.parser
import pydantic
import pydantic.types as pytypes

# The Patient features that can be used for comparison.
FEATURE = typing.Literal[
    "birthdate",
    "mrn",
    "sex",
    "first_name",
    "last_name",
    "line",
    "city",
    "state",
    "zip",
]


class Sex(enum.Enum):
    """
    Enum for the Patient.sex field.
    """

    M = "MALE"
    F = "FEMLAE"
    U = "UNKNOWN"


class Name(pydantic.BaseModel):
    """
    The schema for a name record.
    """

    family: str
    given: typing.List[str] = []
    use: typing.Optional[str] = None
    prefix: typing.List[str] = []  # future use
    suffix: typing.List[str] = []  # future use


class Address(pydantic.BaseModel):
    """
    The schema for an address record.
    """

    line: typing.List[str] = []
    city: typing.Optional[str] = None
    state: typing.Optional[str] = None
    postal_code: typing.Optional[str] = None
    county: typing.Optional[str] = None  # future use
    country: typing.Optional[str] = None


class Telecom(pydantic.BaseModel):
    """
    The schema for a telecom record.
    """

    value: str  # future use
    system: typing.Optional[str] = None
    use: typing.Optional[str] = None


class PIIRecord(pydantic.BaseModel):
    """
    The schema for a PII record.
    """

    internal_id: typing.Optional[uuid.UUID] = None
    birthdate: typing.Optional[pytypes.PastDate] = None
    sex: typing.Optional[Sex] = None
    mrn: typing.Optional[str] = None
    address: typing.List[Address] = []
    name: typing.List[Name] = []
    telecom: typing.List[Telecom] = []

    @pydantic.field_validator("birthdate", mode="before")
    def parse_birthdate(cls, value):
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

    def field_iter(self, field: FEATURE) -> typing.Iterator[str]:
        """
        Given a field name, return an iterator of all string values for that field.
        """
        if field == "birthdate":
            if self.birthdate:
                yield self.birthdate.strftime("%Y-%m-%d")
        elif field == "mrn":
            if self.mrn:
                yield self.mrn
        elif field == "sex":
            if self.sex:
                yield self.sex.name.lower()
        elif field == "line":
            for address in self.address:
                for line in address.line:
                    if line:
                        yield line
        elif field == "city":
            for address in self.address:
                if address.city:
                    yield address.city
        elif field == "state":
            for address in self.address:
                if address.state:
                    yield address.state
        # FIXME: can we change this to "zipcode" some day
        elif field == "zip":
            for address in self.address:
                if address.postal_code:
                    # only use the first 5 digits for comparison
                    yield address.postal_code[:5]
        elif field == "first_name":
            for name in self.name:
                for given in name.given:
                    if given:
                        yield given
        elif field == "last_name":
            for name in self.name:
                if name.family:
                    yield name.family
