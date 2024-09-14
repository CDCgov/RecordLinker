import uuid

from sqlalchemy import orm, ForeignKey, String, JSON


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
