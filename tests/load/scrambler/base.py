from abc import ABC
from abc import abstractmethod


class BaseScrambler(ABC):
    @abstractmethod
    def scramble(self) -> dict:
        """
        Apply scrambling to the record and return the modified version.
        """
        pass
