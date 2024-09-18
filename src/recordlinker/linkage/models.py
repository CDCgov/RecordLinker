import enum
import typing
import uuid

import dotenv
from sqlalchemy import create_engine
from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types as sqltypes


def get_session() -> orm.Session:
    """
    Creates a new session to the MPI database and returns it.
    """
    db_uri = dotenv.dotenv_values()["DB_URI"]
    if not db_uri:
        raise ValueError("DB_URI environment variable not set")
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    return orm.Session(engine)


class Base(orm.DeclarativeBase):
    pass


class Person(Base):
    __tablename__ = "mpi_person"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    internal_id: orm.Mapped[uuid.UUID] = orm.mapped_column(default=uuid.uuid4)


class ExternalPerson(Base):
    __tablename__ = "mpi_external_person"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    person_id: orm.Mapped[int] = orm.mapped_column(schema.ForeignKey("mpi_person.id"))
    external_id: orm.Mapped[str] = orm.mapped_column(sqltypes.String(255))
    source: orm.Mapped[str] = orm.mapped_column(sqltypes.String(255))


class Patient(Base):
    __tablename__ = "mpi_patient"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    person_id: orm.Mapped[int] = orm.mapped_column(schema.ForeignKey("mpi_person.id"))
    data: orm.Mapped[dict] = orm.mapped_column(sqltypes.JSON)


class BlockingKey(enum.Enum):
    """
    Enum for the different types of blocking keys that can be used for patient
    matching. This is the universe of all possible blocking keys that a user can 
    choose from when configuring their algorithm.  When data is loaded into the
    MPI, all possible BlockingValues will be created for the defined BlockingKeys.
    However, only a subset will be used in matching, based on the configuration of
    the algorithm.  By defining them all upfront, we give the user flexibility in
    adjusting their algorithm configuration without having to reload the data.

    **HERE BE DRAGONS**: IN A REAL SYSTEM, THESE ENUMS SHOULD NOT BE CHANGED!!!
    """
    BIRTHDATE = 1, "Date of Birth"
    MRN = 2, "Last 4 chars of MRN"
    SEX = 3, "Gender"
    ZIP = 4, "Zip Code"
    FIRST_NAME = 5, "First 4 chars of First Name"
    LAST_NAME = 6, "First 4 chars of Last Name"

    def __init__(self, id: int, description: str):
        self.id = id
        self.description = description

    def to_value(self, data: dict) -> typing.Generator[str, None, None]:
        """
        Given a data dictionary of Patient PII data, return a generator of all
        possible values for this Key.  Many Keys will only have 1 possible value,
        but some (like first name) could have multiple values.
        """
        if self == BlockingKey.BIRTHDATE:
            if "birthdate" in data:
                yield data["birthdate"].isoformat()
        if self == BlockingKey.MRN:
            if "mrn" in data:
                yield data["mrn"][-4:]
        if self == BlockingKey.SEX:
            if "sex" in data:
                # TODO: Normalize this
                yield data["sex"]
        if self == BlockingKey.ZIP:
            for address in data.get("address", []):
                if "zip" in address:
                    yield address["zip"]
        if self == BlockingKey.FIRST_NAME:
            for name in data.get("name", []):
                for given in name.get("given", []):
                    yield given[:4]
        if self == BlockingKey.LAST_NAME:
            for name in data.get("name", []):
                if "family" in name:
                    yield name.get("family")[:4]


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
    blockingkey: orm.Mapped[int] = orm.mapped_column(sqltypes.Integer)
    value: orm.Mapped[str] = orm.mapped_column(sqltypes.String(50), index=True)
