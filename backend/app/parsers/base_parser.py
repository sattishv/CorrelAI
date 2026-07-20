from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseParser(ABC):
    @abstractmethod
    def validate(self, source: Path | str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, source: Path | str) -> list[Any]:
        raise NotImplementedError