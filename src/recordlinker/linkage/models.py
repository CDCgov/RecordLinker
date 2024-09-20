import datetime
import enum
import typing
import uuid

import dateutil.parser
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types as sqltypes

from recordlinker.config import settings


def get_session() -> orm.Session:
    """
    Creates a new session to the MPI database and returns it.
    """
    engine = create_engine(settings.db_uri)
    Base.metadata.create_all(engine)
    return orm.Session(engine)


class Base(orm.DeclarativeBase):
    pass


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
        if self == BlockingKey.BIRTHDATE:
            vals.update(self._extract_birthdate(data))
        if self == BlockingKey.MRN:
            vals.update(self._extract_mrn_last4(data))
        if self == BlockingKey.SEX:
            vals.update(self._extract_sex(data))
        if self == BlockingKey.ZIP:
            vals.update(self._extract_zipcode(data))
        if self == BlockingKey.FIRST_NAME:
            vals.update(self._extract_first_name_first4(data))
        if self == BlockingKey.LAST_NAME:
            vals.update(self._extract_last_name_first4(data))

        # remove all empty strings from the set, we never want to block on these
        vals.discard("")
        return vals

    # FIXME: some of the type/isinstance checks below can be removed after we create
    # a serializer to capture the input data, as type dict is too flexible
    def _extract_birthdate(self, data: dict) -> typing.Iterator[str]:
        val = data.get("birthdate")
        if val:
            if not isinstance(val, (datetime.date, datetime.datetime)):
                # if not an instance of date or datetime, try to parse it
                val = dateutil.parser.parse(str(val))
            yield val.strftime("%Y-%m-%d")

    def _extract_mrn_last4(self, data: dict) -> typing.Iterator[str]:
        if data.get("mrn"):
            yield data["mrn"].strip()[-4:]

    def _extract_sex(self, data: dict) -> typing.Iterator[str]:
        if data.get("sex"):
            val = str(data["sex"]).lower().strip()
            if val in ["m", "male"]:
                yield "m"
            elif val in ["f", "female"]:
                yield "f"
            else:
                yield "u"

    def _extract_zipcode(self, data: dict) -> typing.Iterator[str]:
        val = data.get("address")
        if isinstance(val, (list, set)):
            for address in val:
                if isinstance(address, dict):
                    if address.get("zip"):
                        yield str(address["zip"]).strip()[0:5]

    def _extract_first_name_first4(self, data: dict) -> typing.Iterator[str]:
        val = data.get("name")
        if isinstance(val, (list, set)):
            for name in val:
                if isinstance(name, dict):
                    for given in name.get("given", []):
                        if given:
                            yield str(given)[:4]

    def _extract_last_name_first4(self, data: dict) -> typing.Iterator[str]:
        val = data.get("name")
        if isinstance(val, (list, set)):
            for name in val:
                if isinstance(name, dict):
                    if name.get("family"):
                        yield str(name["family"])[:4]


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


class Algorithm(Base):
    __tablename__ = "algorithm"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    is_default: orm.Mapped[bool] = orm.mapped_column(default=False, index=True)
    label: orm.Mapped[str] = orm.mapped_column(sqltypes.String(255), unique=True)
    description: orm.Mapped[str] = orm.mapped_column(sqltypes.Text())


def check_only_one_default(mapping, connection, target):
    """
    Check if there is already a default algorithm before inserting or updating.
    If another default algorithm exists, an exception is raised to prevent the operation.

    Parameters:
    connection: The database connection being used for the operation.
    target: The instance of the Algorithm class being inserted or updated.

    Raises:
    ValueError: If another algorithm is already marked as default.
    """

    session = orm.Session.object_session(target)

    if target.is_default:
        # ruff linting rule E712 ignored on this line.
        # ruff wants to enforce using the 'is' operator over '=='.
        # However since we only want to compare the truth value of the SQL query result we need to use '=='.
        existing = session.query(Algorithm).filter(Algorithm.is_default == True).first()  # noqa: E712

        if existing and existing.id != target.id:
            raise ValueError("There can only be one default algorithm")


event.listen(Algorithm, "before_insert", check_only_one_default)
event.listen(Algorithm, "before_update", check_only_one_default)


class AlgorithmPass(Base):
    __tablename__ = "algorithm_pass"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    algorithm_id: orm.Mapped[int] = orm.mapped_column(schema.ForeignKey("algorithm.id"))
    blocking_keys: orm.Mapped[list[int]] = orm.mapped_column(sqltypes.JSON)
    evaluators: orm.Mapped[list[str]] = orm.mapped_column(sqltypes.JSON)
    rule: orm.Mapped[str] = orm.mapped_column(sqltypes.String(255))
    cluster_ratio: orm.Mapped[float] = orm.mapped_column(sqltypes.Float)
    kwargs: orm.Mapped[dict] = orm.mapped_column(sqltypes.JSON)
