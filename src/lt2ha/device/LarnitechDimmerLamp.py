from dataclasses import dataclass
from typing import Any

from .LarnitechLamp import LarnitechLamp


@dataclass(frozen=True, init=False)
class LarnitechDimmerLamp(LarnitechLamp):
    def _setup_(self) -> None:
        super()._setup_()
        self.config.update({
            "brightness_scale": 100,
            "brightness_command_topic": "level",
            "brightness_state_topic": "level",
        })

    def notify_ha(self) -> dict[str, Any]:
        return {
            **super().notify_ha(),
            "brightness_state_topic": self.status["level"],
        }


__all__ = [
    "LarnitechDimmerLamp",
]
