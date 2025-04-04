import enum
import uuid

from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types as sqltypes

from .base import Base
from .base import get_bigint_pk

# The maximum length of a blocking value, we want to optimize this to be as small
# as possible to reduce the amount of data stored in the database.  However, it needs
# to be long enough to store the longest possible value for a blocking key.
BLOCKING_VALUE_MAX_LENGTH = 20


class Person(Base):
    __tablename__ = "mpi_person"

    id: orm.Mapped[int] = orm.mapped_column(get_bigint_pk(), autoincrement=True, primary_key=True)
    reference_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        default=uuid.uuid4, unique=True, index=True
    )
    patients: orm.Mapped[list["Patient"]] = orm.relationship(back_populates="person")

    def __hash__(self):
        """
        Hash the Person object based on the primary key.
        """
        return hash(self.id)

    def __eq__(self, other):
        """
        Compare two Person objects based on the primary key.
        """
        return self.id == other.id if isinstance(other, Person) else False


class Patient(Base):
    __tablename__ = "mpi_patient"

    id: orm.Mapped[int] = orm.mapped_column(get_bigint_pk(), autoincrement=True, primary_key=True)
    person_id: orm.Mapped[int] = orm.mapped_column(
        schema.ForeignKey(f"{Person.__tablename__}.id"), nullable=True
    )
    person: orm.Mapped["Person"] = orm.relationship(back_populates="patients")
    data: orm.Mapped[dict] = orm.mapped_column(sqltypes.JSON, default=dict)
    external_patient_id: orm.Mapped[str] = orm.mapped_column(sqltypes.String(255), nullable=True)
    external_person_id: orm.Mapped[str] = orm.mapped_column(sqltypes.String(255), nullable=True)
    external_person_source: orm.Mapped[str] = orm.mapped_column(sqltypes.String(100), nullable=True)
    blocking_values: orm.Mapped[list["BlockingValue"]] = orm.relationship(back_populates="patient")
    reference_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        default=uuid.uuid4, unique=True, index=True
    )


class BlockingKey(enum.Enum):
    """
    Enum for the different types of blocking keys that can be used for patient
    matching. This is the universe of all possible blocking keys that a user can
    choose from when configuring their algorithm.  When data is loaded into the
    MPI, all possible BlockingValues will be created for the defined BlockingKeys.
    However, only a subset will be used in matching, based on the configuration of
    the algorithm.  By defining them all upfront, we give the user flexibility in
    adjusting their algorithm configuration without having to reload the data.

    NOTE: The database schema is designed to allow for blocking values up to 20 characters
    in length.  All blocking keys should be designed to fit within this constraint.

    **HERE BE DRAGONS**: IN A PRODUCTION SYSTEM, THESE ENUMS SHOULD NOT BE CHANGED!!!
    """

    BIRTHDATE = ("BIRTHDATE", 1, "Date of birth as YYYY-MM-DD")
    SEX = ("SEX", 3, "Sex at birth; M or F")
    ZIP = ("ZIP", 4, "5 digital US Postal Code")
    FIRST_NAME = ("FIRST_NAME", 5, "First 4 characters of the first name")
    LAST_NAME = ("LAST_NAME", 6, "First 4 characters of the last name")
    ADDRESS = ("ADDRESS", 7, "First 4 characters of the address")
    PHONE = ("PHONE", 8, "Last 4 characters of the phone number")
    EMAIL = ("EMAIL", 9, "First 4 characters of the email address")
    IDENTIFIER = (
        "IDENTIFIER",
        10,
        "A colon separated string of the identifier type, first 2 characters of the authority and last 4 characters of the value",
    )

    def __init__(self, value: str, _id: int, description: str):
        self._value = value
        self.id = _id
        self.description = description

    @property
    def value(self) -> str:
        """
        Return the value of the enum.
        """
        return self._value


class BlockingValue(Base):
    __tablename__ = "mpi_blocking_value"
    # create a composite index on patient_id, blockingkey and value
    __table_args__ = (
        schema.Index("idx_blocking_value_patient_key_value", "patient_id", "blockingkey", "value"),
    )

    id: orm.Mapped[int] = orm.mapped_column(get_bigint_pk(), autoincrement=True, primary_key=True)
    patient_id: orm.Mapped[int] = orm.mapped_column(
        schema.ForeignKey(f"{Patient.__tablename__}.id")
    )
    patient: orm.Mapped["Patient"] = orm.relationship(back_populates="blocking_values")
    blockingkey: orm.Mapped[int] = orm.mapped_column(sqltypes.SmallInteger)
    value: orm.Mapped[str] = orm.mapped_column(sqltypes.String(BLOCKING_VALUE_MAX_LENGTH))
