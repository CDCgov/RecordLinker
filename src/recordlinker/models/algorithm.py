import logging
import typing

from sqlalchemy import event
from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types as sqltypes

from recordlinker import utils
from recordlinker.config import ConfigurationError
from recordlinker.config import settings

from .base import Base

LOGGER = logging.getLogger(__name__)


class Algorithm(Base):
    __tablename__ = "algorithm"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    is_default: orm.Mapped[bool] = orm.mapped_column(default=False, index=True)
    label: orm.Mapped[str] = orm.mapped_column(sqltypes.String(255), unique=True)
    description: orm.Mapped[str] = orm.mapped_column(sqltypes.Text(), nullable=True)
    passes: orm.Mapped[list["AlgorithmPass"]] = orm.relationship(
        back_populates="algorithm", cascade="all, delete-orphan"
    )

    @classmethod
    def from_dict(cls, **data: dict) -> "Algorithm":
        """
        Create an instance of Algorithm from a dictionary.

        Parameters:
        data: The dictionary containing the data for the Algorithm instance.

        Returns:
        The Algorithm instance.
        """
        data["passes"] = [AlgorithmPass(**p) for p in data.get("passes", [])]
        return cls(**data)


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
    algorithm_id: orm.Mapped[int] = orm.mapped_column(
        schema.ForeignKey("algorithm.id", ondelete="CASCADE")
    )
    algorithm: orm.Mapped["Algorithm"] = orm.relationship(back_populates="passes")
    blocking_keys: orm.Mapped[list[str]] = orm.mapped_column(sqltypes.JSON)
    _evaluators: orm.Mapped[dict[str, str]] = orm.mapped_column("evaluators", sqltypes.JSON)
    _rule: orm.Mapped[str] = orm.mapped_column("rule", sqltypes.String(255))
    cluster_ratio: orm.Mapped[float] = orm.mapped_column(sqltypes.Float)
    kwargs: orm.Mapped[dict] = orm.mapped_column(sqltypes.JSON, default=dict)

    @property
    def evaluators(self) -> dict[str, str]:
        """
        Get the evaluators for this algorithm pass.
        """
        return self._evaluators

    @evaluators.setter  # type: ignore
    def evaluators(self, value: dict[str, str]):
        """
        Set the evaluators for this algorithm pass.
        """
        self._evaluators = value
        if hasattr(self, "_bound_evaluators"):
            del self._bound_evaluators

    def bound_evaluators(self) -> dict[str, typing.Callable]:
        """
        Get the evaluators for this algorithm pass, bound to the algorithm.
        """
        if not hasattr(self, "_bound_evaluators"):
            self._bound_evaluators = utils.bind_functions(self.evaluators)
        return self._bound_evaluators

    @property
    def rule(self) -> str:
        """
        Get the rule for this algorithm pass.
        """
        return self._rule

    @rule.setter  # type: ignore
    def rule(self, value: str):
        """
        Set the rule for this algorithm pass.
        """
        self._rule = value
        if hasattr(self, "_bound_rule"):
            del self._bound_rule

    def bound_rule(self) -> typing.Callable:
        """
        Get the rule for this algorithm pass, bound to the algorithm.
        """
        if not hasattr(self, "_bound_rule"):
            self._bound_rule = utils.str_to_callable(self.rule)
        return self._bound_rule


@event.listens_for(schema.MetaData, "after_create")
def create_initial_algorithms(target, connection, **kw) -> typing.List[Algorithm]:
    """
    Create the initial algorithms if they have been defined in the configuration.
    This function is called after the database schema has been created in the
    recordlinker.database.create_sessionmaker function.
    """
    LOGGER.warning(f"VALUE: {settings.initial_algorithms}")
    if settings.initial_algorithms:
        try:
            data = utils.read_json(settings.initial_algorithms)
        except Exception as exc:
            raise ConfigurationError(f"Error loading initial algorithms: {exc}")
        if not any(algo["is_default"] for algo in data):
            raise ConfigurationError(f"No default algorithm found in {settings.initial_algorithms}")

        session = orm.Session(bind=connection)
        try:
            # Only load the algorithms if there are none in the database
            if session.query(Algorithm).count() == 0:
                objs = [Algorithm.from_dict(**algo) for algo in data]
                session.add_all(objs)
                session.commit()
                LOGGER.info(f"Created {len(objs)} initial algorithms.")
                return objs
        except Exception as exc:
            session.rollback()
            raise exc
        finally:
            session.close()
