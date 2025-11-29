from dataclasses import dataclass

from .LarnitechDevice import LarnitechDevice


@dataclass(frozen=True, init=False)
class LarnitechHumiditySensor(LarnitechDevice):
    def _setup_(self) -> None:
        super()._setup_()
        self.config.update({
            "state_class": "measurement",
            "device_class": "humidity",
            "unit_of_measurement": "%",
        })


__all__ = [
    "LarnitechHumiditySensor",
]
