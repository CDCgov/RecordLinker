import typing

from sqlalchemy import event
from sqlalchemy import orm
from sqlalchemy import schema
from sqlalchemy import types as sqltypes

from recordlinker import utils

from .base import Base


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
        data["passes"] = [AlgorithmPass(**p) for p in data["passes"]]
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
