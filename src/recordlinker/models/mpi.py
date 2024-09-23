import enum
import uuid

from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types as sqltypes

from . import Base
from .pii import PIIRecord


class Person(Base):
    __tablename__ = "mpi_person"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    internal_id: orm.Mapped[uuid.UUID] = orm.mapped_column(default=uuid.uuid4)
    patients: orm.Mapped[list["Patient"]] = orm.relationship(back_populates="person")


class Patient(Base):
    __tablename__ = "mpi_patient"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    person_id: orm.Mapped[int] = orm.mapped_column(schema.ForeignKey("mpi_person.id"))
    person: orm.Mapped["Person"] = orm.relationship(back_populates="patients")
    data: orm.Mapped[dict] = orm.mapped_column(sqltypes.JSON)
    external_patient_id: orm.Mapped[str] = orm.mapped_column(
        sqltypes.String(255), nullable=True
    )
    external_person_id: orm.Mapped[str] = orm.mapped_column(
        sqltypes.String(255), nullable=True
    )
    external_person_source: orm.Mapped[str] = orm.mapped_column(
        sqltypes.String(100), nullable=True
    )
    blocking_values: orm.Mapped[list["BlockingValue"]] = orm.relationship(
        back_populates="patient"
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

    **HERE BE DRAGONS**: IN A PRODUCTION SYSTEM, THESE ENUMS SHOULD NOT BE CHANGED!!!
    """

    BIRTHDATE = 1, "Date of Birth"
    MRN = 2, "Last 4 chars of MRN"
    SEX = 3, "Sex"
    ZIP = 4, "Zip Code"
    FIRST_NAME = 5, "First 4 chars of First Name"
    LAST_NAME = 6, "First 4 chars of Last Name"

    def __init__(self, id: int, description: str):
        self.id = id
        self.description = description

    def to_value(self, data: dict) -> set[str]:
        """
        Given a data dictionary of Patient PII data, return a set of all
        possible values for this Key.  Many Keys will only have 1 possible value,
        but some (like first name) could have multiple values.
        """
        vals: set[str] = set()

        pii = PIIRecord(**data)
        if self == BlockingKey.BIRTHDATE:
            vals.update(pii.field_iter("birthdate"))
        if self == BlockingKey.MRN:
            vals.update({x[-4:] for x in pii.field_iter("mrn")})
        if self == BlockingKey.SEX:
            vals.update(pii.field_iter("sex"))
        if self == BlockingKey.ZIP:
            vals.update(pii.field_iter("zipcode"))
        if self == BlockingKey.FIRST_NAME:
            vals.update({x[:4] for x in pii.field_iter("first_name")})
        if self == BlockingKey.LAST_NAME:
            vals.update({x[:4] for x in pii.field_iter("last_name")})

        # remove all empty strings from the set, we never want to block on these
        vals.discard("")
        return vals


class BlockingValue(Base):
    __tablename__ = "mpi_blocking_value"
    # create a composite index on patient_id, blockingkey and value
    __table_args__ = (
        schema.Index(
            "idx_blocking_value_patient_key_value", "patient_id", "blockingkey", "value"
        ),
    )

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    patient_id: orm.Mapped[int] = orm.mapped_column(schema.ForeignKey("mpi_patient.id"))
    patient: orm.Mapped["Patient"] = orm.relationship(back_populates="blocking_values")
    blockingkey: orm.Mapped[int] = orm.mapped_column(sqltypes.Integer)
    value: orm.Mapped[str] = orm.mapped_column(sqltypes.String(50))
