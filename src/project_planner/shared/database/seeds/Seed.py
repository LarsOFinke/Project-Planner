from abc import ABC, abstractmethod

from sqlalchemy.orm import Session


class Seed(ABC):
    @property
    @abstractmethod
    def key(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def apply(self, session: Session) -> None:
        raise NotImplementedError
