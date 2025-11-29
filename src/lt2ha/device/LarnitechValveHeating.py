from dataclasses import dataclass
from typing import Any, ClassVar

from .LarnitechDevice import LarnitechDevice


@dataclass(frozen=True, init=False)
class LarnitechValveHeating(LarnitechDevice):
    entity_type: ClassVar[str] = "climate"

    automations: list[str]

    def _setup_(self) -> None:
        super()._setup_()

        self.config.pop("state_topic")
        self.config.update({
            "mode_command_topic": "mode",
            "mode_state_topic": "mode",
            "preset_mode_command_topic": "preset",
            "preset_mode_state_topic": "preset",
            "temperature_command_topic": "temperature",
            "temperature_state_topic": "temperature",
            "current_temperature_topic": "current_temperature",
            "modes": ["off", "heat"],
            "preset_modes": self.automations,
            "temp_step": 0.5,
            "min_temp": 15,
            "max_temp": 35,
            "temperature_unit": "C",
        })

    def notify_ha(self) -> dict[str, Any]:
        values = {}
        automation = self.status.get("automation")

        # The LT `automation`'s analogue in HA is a preset.
        # The `always-off` is coming as the `automation` prop
        # but really marks the device being off. When the `state`
        # is `off`, that means the LT just closed the heating
        # valve, and it may open any time when the temp drops
        # below the target.
        #
        # Though it's also seen that the `state=off` may mark
        # the device being really off when there are no extra
        # properties along it.
        if automation == "always-off" or (self.status["state"] == "off" and len(self.status) == 1):
            values.update({
                "mode_state_topic": "off",
                "preset_mode_state_topic": "None",
            })
        elif automation:
            values.update({
                "mode_state_topic": "heat",
                "preset_mode_state_topic": self.status["automation"],
            })

        for prop, topic in (
            ("current", "current_temperature_topic"),
            # No `target` for `status.automation = always-off`.
            ("target", "temperature_state_topic"),
        ):
            temperature = self.status.get(prop)

            if temperature:
                values[topic] = temperature

        return values

    def notify_lt(self, attr: str | None, value: Any) -> dict[str, Any] | tuple[tuple[str, dict[str, Any]], ...]:
        if attr == "mode":
            if value == "heat":
                return {
                    "state": "on",
                    "automation": self.automations[0],
                }

            if value == "off":
                return {
                    "state": "off",
                    "automation": "always-off",
                }

        if attr == "preset":
            return {
                "state": "on",
                "automation": value,
            }

        if attr == "temperature":
            return {
                "target": value,
            }

        assert False


__all__ = [
    "LarnitechValveHeating",
]
