from dataclasses import dataclass

from .LarnitechDevice import LarnitechDevice


@dataclass(frozen=True, init=False)
class LarnitechTemperatureSensor(LarnitechDevice):
    def _setup_(self) -> None:
        super()._setup_()
        self.config.update({
            "state_class": "measurement",
            "device_class": "temperature",
            "unit_of_measurement": "°C",
        })


__all__ = [
    "LarnitechTemperatureSensor",
]
