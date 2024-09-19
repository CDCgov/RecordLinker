import uuid

from sqlalchemy import event
from sqlalchemy import ForeignKey
from sqlalchemy import JSON
from sqlalchemy import orm
from sqlalchemy import String
from sqlalchemy import Text


class Base(orm.DeclarativeBase):
    pass

class Person(Base):
    __tablename__ = "mpi_person"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    internal_id: orm.Mapped[uuid.UUID] = orm.mapped_column(default=uuid.uuid4)

class ExternalPerson(Base):
    __tablename__ = "mpi_external_person"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    person_id: orm.Mapped[int] = orm.mapped_column(ForeignKey("mpi_person.id"))
    external_id: orm.Mapped[str] = orm.mapped_column(String(255))
    source: orm.Mapped[str] = orm.mapped_column(String(255))

class Patient(Base):
    __tablename__ = "mpi_patient"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    person_id: orm.Mapped[int] = orm.mapped_column(ForeignKey("mpi_person.id"))
    data: orm.Mapped[dict] = orm.mapped_column(JSON)

class BlockingKey(Base):
    __tablename__ = "mpi_blocking_key"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(String(50), index=True)

class BlockingValue(Base):
    __tablename__ = "mpi_blocking_value"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    patient_id: orm.Mapped[int] = orm.mapped_column(ForeignKey("mpi_patient.id"))
    blockingkey_id: orm.Mapped[int] = orm.mapped_column(ForeignKey("mpi_blocking_key.id"))
    value: orm.Mapped[str] = orm.mapped_column(String(50), index=True)

class Algorithm(Base):
    __tablename__ = "algorithm"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True, index=True)
    is_default: orm.Mapped[bool] = orm.mapped_column(default=False)
    label: orm.Mapped[str] = orm.mapped_column(String(255), unique=True)
    description: orm.Mapped[str] = orm.mapped_column(Text())

def check_only_one_default(target):
    """
    Check if there is already a default algorithm before inserting or updating.
    If another default algorithm exists, an exception is raised to prevent the operation.
    
    Parameters:
    connection: The database connection being used for the operation.
    target: The instance of the Algorithm class being inserted or updated.
    
    Raises:
    Exception: If another algorithm is already marked as default.
    """
    session = orm.Session.object_session(target)
  
    if target.is_default:
        existing = session.query(Algorithm).filter(Algorithm.is_default is True).first()
      
        if existing and existing.id != target.id:
            raise ValueError("There can only be one default algorithm")

event.listen(Algorithm, 'before_insert', check_only_one_default)
event.listen(Algorithm, 'before_update', check_only_one_default)

class AlgorithmPass(Base):
    __tablename__ = "algorithm_pass"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    algorithm_id: orm.Mapped[int] = orm.mapped_column(ForeignKey("algorithm.id"))
    blocking_keys: orm.Mapped[list[int]] = orm.mapped_column(JSON)
    evaluators: orm.Mapped[list[str]] = orm.mapped_column(JSON)     
    rule: orm.Mapped[str] = orm.mapped_column(String(255))
    cluster_ratio: orm.Mapped[float]
    kwargs: orm.Mapped[dict] = orm.mapped_column(JSON)
