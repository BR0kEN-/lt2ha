from dataclasses import dataclass, field, fields, MISSING
from typing import Any, ClassVar


@dataclass(frozen=True, init=False)
class LarnitechDevice:
    entity_type: ClassVar[str] = "sensor"

    addr: str
    name: str
    area: str
    type: str
    status: dict = field(repr=False)
    config: dict = field(init=False, repr=False)
    extra: dict = field(init=False, repr=False)

    def __init__(self, data: dict) -> None:
        extra = {}
        cls_fields = fields(self)
        defined_fields = {f.name for f in cls_fields}

        for key, value in data.items():
            if key in defined_fields:
                self._setattr(key, value)
            else:
                extra[key] = value

        # Ensure all required fields (without defaults) are set.
        for cls_field in cls_fields:
            if cls_field.name not in data:
                if cls_field.default is MISSING:
                    if cls_field.default_factory is MISSING:
                        if cls_field.init:
                            raise TypeError(f"Missing required argument: '{cls_field.name}'")
                    else:
                        self._setattr(cls_field.name, cls_field.default_factory())
                else:
                    self._setattr(cls_field.name, cls_field.default)

        self._setattr(
            name="extra",
            value=extra,
        )
        self._setattr(
            name="config",
            value={
                "state_topic": "",
            },
        )

        self._setup_()

    def _setup_(self) -> None:
        pass

    def _setattr(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)

    def set_status(self, status: dict, addr: str) -> None:
        assert self.addr == addr
        self._setattr("status", status)

    def notify_ha(self) -> dict[str, Any]:
        """
        Supplies the current value from Larnitech to Home Assistant.

        :return: The key of the returning `dict` must exist in `self.config`,
         end with the `_topic` but not the `command_topic`, and reference the
         real MQTT topic where Home Assistant expects the published value.
        """
        # Some entities (i.e. of `virtual` type) have props
        # other than the `state`. Ideally, there should be
        # separate devices for them.
        state = self.status.get("state")

        if not state:
            return {}

        return {
            "state_topic": state,
        }

    # noinspection PyMethodMayBeStatic, PyUnusedLocal
    def notify_lt(self, attr: str | None, value: Any) -> dict[str, Any] | tuple[tuple[str, dict[str, Any]], ...]:
        """
        Supplies the current value from Home Assistant to Larnitech.

        :return: Either the `status` for the current device `addr`, or a tuple
         where each item's `0` member is the `addr` of the device in control,
         and `1` member - the `status` dict for that `addr`. The `tuple` form
         is only relevant for wrappers that controls several devices.
        """
        return {
            "state": value,
        }


__all__ = [
    "LarnitechDevice",
]
