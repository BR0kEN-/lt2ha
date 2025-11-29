from dataclasses import dataclass
from websockets import connect


@dataclass(frozen=True)
class LarnitechConfig:
    host: str
    """
    The Larnitech server hostname or IP.
    """

    port: int
    """
    The Websocket server port.

    Can be seen at `http://{host}/#settings_general` (hit the `API` button).
    """

    key: str
    """
    The API key.

    Enable access to the API and get the key at `http://{host}/#settings_security`.
    """

    ignored_addrs: tuple[str, ...]
    """
    The list of specific devices to not add to HA (use `addr` to identify the
    device in Larnitech).
    """

    ignored_types: tuple[str, ...]
    """
    The list of device types to not add to HA.
    """

    ignored_areas: tuple[str, ...]
    """
    The list of Larnitech area names the devices from which will not be added
    to HA (case-insensitive).
    """

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "ignored_areas",
            tuple(map(lambda a: a.lower(), self.ignored_areas)),
        )

    def connect(self) -> connect:
        return connect(
            f"ws://{self.host}:{self.port}/api",
            max_size=10 * 1024 * 1024,
            close_timeout=10,
            ping_interval=None,
            ping_timeout=None,
        )


__all__ = [
    "LarnitechConfig",
]
