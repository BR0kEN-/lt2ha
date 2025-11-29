from dataclasses import dataclass
from typing import Any, ClassVar

from .LarnitechDeviceWrapper import LarnitechDeviceWrapper
from .LarnitechAirFan import LarnitechAirFan


# @todo: We're lucky enough that in the current LT setup the speeds are in the correct sequence
#        so it's possible to use speed as an index. This is fragile. Need a way to say "this is speed X".
@dataclass(frozen=True, init=False)
class LarnitechAirFanMultispeed(LarnitechDeviceWrapper[LarnitechAirFan]):
    entity_type: ClassVar[str] = "fan"

    def _setup_(self) -> None:
        super()._setup_()
        self.config.update({
            "command_topic": "state",
            "state_topic": "state",
            "payload_on": "on",
            "payload_off": "off",
            "percentage_command_topic": "speed",
            "percentage_state_topic": "speed",
            "speed_range_min": 1,
            "speed_range_max": 2,
        })

    def notify_ha(self) -> dict[str, Any]:
        active: str | None = None
        item_speed = 0

        for addr, status in self.status.items():
            item_speed += 1

            if status["state"] == self.config["payload_on"]:
                active = addr
                break

        return {
            "state_topic": self.config[f"payload_{'on' if active else 'off'}"],
            "percentage_state_topic": item_speed if active else 0,
        }

    def notify_lt(self, attr: str | None, value: Any) -> dict[str, Any] | tuple[tuple[str, dict[str, Any]], ...]:
        if attr == "state":
            value = self.config["speed_range_min"] if value == self.config["payload_on"] else 0
        else:
            assert attr == "speed"

        item_speed = 0
        selected_speed = int(value)
        values = []

        for addr, status in self.status.items():
            item_speed += 1
            values.append(
                (
                    addr,
                    {
                        **status,
                        "state": self.config[f"payload_{"on" if item_speed == selected_speed else "off"}"],
                    },
                ),
            )

        # Ensure the `off` commands are sent first. This is relevant during
        # the transition from higher to lower speed. Without sorting, the
        # command to enable the lower speed is sent first, followed by another
        # one to turn off the higher speed. For a moment, both speeds are on,
        # which is potentially dangerous (depending on the air fan wiring).
        return tuple(sorted(values, key=lambda x: x[1]["state"] != self.config["payload_off"]))


__all__ = [
    "LarnitechAirFanMultispeed",
]
