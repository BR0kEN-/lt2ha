from dataclasses import dataclass
from typing import Any, ClassVar

from .LarnitechDevice import LarnitechDevice


@dataclass(frozen=True, init=False)
class LarnitechMotionSensor(LarnitechDevice):
    entity_type: ClassVar[str] = "binary_sensor"

    def _setup_(self) -> None:
        super()._setup_()
        self.config.update({
            "device_class": "motion",
            "payload_on": "on",
            "payload_off": "off",
        })

    def notify_ha(self) -> dict[str, Any]:
        return {
            "state_topic": self.config[f"payload_{self._get_ha_state()}"]
        }

    def _get_ha_state(self) -> str:
        # The `state` for this sensor in Larnitech is a floating
        # number that indicates the detected movement percentage.
        return "on" if self.status["state"] > 0 else "off"


__all__ = [
    "LarnitechMotionSensor",
]
