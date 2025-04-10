import dataclasses
import logging
import typing

from sqlalchemy import event
from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types as sqltypes

from recordlinker.config import ConfigurationError
from recordlinker.config import settings
from recordlinker.utils import path as path_utils

from .base import Base

LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class BoundEvaluator:
    """
    The schema for a bound evaluator record.
    """

    feature: str
    func: typing.Callable


class Algorithm(Base):
    __tablename__ = "algorithm"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    is_default: orm.Mapped[bool] = orm.mapped_column(default=False, index=True)
    label: orm.Mapped[str] = orm.mapped_column(sqltypes.String(255), unique=True)
    description: orm.Mapped[str] = orm.mapped_column(sqltypes.Text(), nullable=True)
    include_multiple_matches: orm.Mapped[bool] = orm.mapped_column(sqltypes.Boolean, default=True)
    passes: orm.Mapped[list["AlgorithmPass"]] = orm.relationship(
        back_populates="algorithm", cascade="all, delete-orphan"
    )
    max_missing_allowed_proportion: orm.Mapped[float] = orm.mapped_column(
        sqltypes.Float, default=0.5
    )
    missing_field_points_proportion: orm.Mapped[float] = orm.mapped_column(
        sqltypes.Float, default=0.5
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
        passes = [AlgorithmPass(**p) for p in data.pop("passes", [])]
        return cls(passes=passes, **data)


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
    label: orm.Mapped[str] = orm.mapped_column(sqltypes.String(255), nullable=True)
    description: orm.Mapped[str] = orm.mapped_column(sqltypes.Text(), nullable=True)
    algorithm_id: orm.Mapped[int] = orm.mapped_column(
        schema.ForeignKey(f"{Algorithm.__tablename__}.id", ondelete="CASCADE")
    )
    algorithm: orm.Mapped["Algorithm"] = orm.relationship(back_populates="passes")
    blocking_keys: orm.Mapped[list[str]] = orm.mapped_column(sqltypes.JSON)
    minimum_match_threshold: orm.Mapped[float] = orm.mapped_column(sqltypes.Float, default=1.0)
    certain_match_threshold: orm.Mapped[float] = orm.mapped_column(sqltypes.Float, default=1.0)
    _evaluators: orm.Mapped[list[dict]] = orm.mapped_column("evaluators", sqltypes.JSON)
    kwargs: orm.Mapped[dict] = orm.mapped_column(sqltypes.JSON, default=dict)

    @property
    def possible_match_window(self) -> tuple[float, float]:
        """
        Get the Possible Match Window for this algorithm pass.
        """
        return (self.minimum_match_threshold, self.certain_match_threshold)

    @possible_match_window.setter  # type: ignore
    def possible_match_window(self, value: tuple[float, float]):
        """
        Set the Possible Match Window for this algorithm pass. The Possible Match Window
        is made up of the interval between the Minimum Match Threshold and the Certain
        Match Threshold.
        """
        self.minimum_match_threshold, self.certain_match_threshold = value

    @property
    def evaluators(self) -> list[dict]:
        """
        Get the evaluators for this algorithm pass.
        """
        return self._evaluators

    @evaluators.setter  # type: ignore
    def evaluators(self, value: list[dict]):
        """
        Set the evaluators for this algorithm pass.
        """
        self._evaluators = value
        if hasattr(self, "_bound_evaluators"):
            del self._bound_evaluators

    def bound_evaluators(self) -> list[BoundEvaluator]:
        """
        Get the evaluators for this algorithm pass, bound to the algorithm.
        """
        # NOTE: This is a temp fix to avoid circular import,
        # this will be removed when issue #223 is completed
        from recordlinker.linking import matchers

        if not hasattr(self, "_bound_evaluators"):
            self._bound_evaluators: list[BoundEvaluator] = []
            for e in self.evaluators:
                try:
                    fn = getattr(matchers.FeatureFunc, e["func"]).callable()
                except AttributeError:
                    raise ValueError("Failed to convert string to callable")
                self._bound_evaluators.append(
                    BoundEvaluator(**{"feature": e["feature"], "func": fn})
                )
        return self._bound_evaluators


@event.listens_for(schema.MetaData, "after_create")
def create_initial_algorithms(target, connection, **kw) -> typing.List[Algorithm] | None:
    """
    Create the initial algorithms if they have been defined in the configuration.
    This function is called after the database schema has been created in the
    recordlinker.database.create_sessionmaker function.
    """
    if settings.initial_algorithms:
        try:
            data = path_utils.read_json(settings.initial_algorithms)
        except Exception as exc:
            raise ConfigurationError("Error loading initial algorithms") from exc
        if not any(algo.get("is_default") for algo in data):
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
            raise ConfigurationError("Error creating initial algorithms") from exc
        finally:
            session.close()
    return None
