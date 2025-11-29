from dataclasses import dataclass

from .LarnitechMotionSensor import LarnitechMotionSensor


@dataclass(frozen=True, init=False)
class LarnitechLeakSensor(LarnitechMotionSensor):
    def _setup_(self) -> None:
        super()._setup_()
        self.config.update({
            "device_class": "moisture",
            "payload_on": "leakage",
            "payload_off": "ok",
        })

    def _get_ha_state(self) -> str:
        # This sensor's value is inversed in HA.
        return "off" if self.status["state"] == "ok" else "on"


__all__ = [
    "LarnitechLeakSensor",
]
