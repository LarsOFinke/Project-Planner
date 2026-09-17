from typing import Protocol


class SystemHealthProbe(Protocol):
    @property
    def database_backend(self) -> str: ...

    @property
    def database_location(self) -> str: ...

    def is_healthy(self) -> bool: ...
