from dataclasses import dataclass
from typing import ClassVar

from .LarnitechDevice import LarnitechDevice


@dataclass(frozen=True, init=False)
class LarnitechValve(LarnitechDevice):
    entity_type: ClassVar[str] = "valve"

    def _setup_(self) -> None:
        super()._setup_()
        self.config.update({
            "command_topic": "",
            "state_topic": "",
            "state_open": "opened",
            "state_closed": "closed",
            "payload_open": "open",
            "payload_close": "close",
        })


__all__ = [
    "LarnitechValve",
]
