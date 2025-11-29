from dataclasses import dataclass
from typing import ClassVar

from .LarnitechDevice import LarnitechDevice


@dataclass(frozen=True, init=False)
class LarnitechToggleable(LarnitechDevice):
    entity_type: ClassVar[str] = "switch"

    def _setup_(self) -> None:
        super()._setup_()
        self.config.update({
            "command_topic": "",
            "payload_on": "on",
            "payload_off": "off",
        })


__all__ = [
    "LarnitechToggleable",
]
