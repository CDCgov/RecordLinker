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
    # Create a unique index on the combination of person_id and external_id
    __table_args__ = (orm.UniqueConstraint("person_id", "external_id"))

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
    patient_id: orm.Mapped[int] = orm.mapped_column(ForeignKey("mpi_patient.id"))
    key: orm.Mapped[str] = orm.mapped_column(String(50), index=True)
    value: orm.Mapped[str] = orm.mapped_column(String(50), index=True)
