from dataclasses import dataclass
from typing import Any, ClassVar

from .LarnitechDevice import LarnitechDevice


@dataclass(frozen=True, init=False)
class LarnitechAirFan(LarnitechDevice):
    entity_type: ClassVar[str] = "fan"

    def _setup_(self) -> None:
        super()._setup_()
        self.config.update({
            "command_topic": "state",
            "state_topic": "state",
            "payload_on": "on",
            "payload_off": "off",
        })

    def notify_ha(self) -> dict[str, Any]:
        return {
            "state_topic": self.status["state"],
        }

    def notify_lt(self, attr: str | None, value: Any) -> dict[str, Any] | tuple[tuple[str, dict[str, Any]], ...]:
        return {
            attr: value,
            "auto-state": True,
        }


__all__ = [
    "LarnitechAirFan",
]
