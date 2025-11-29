from ..LarnitechConfig import LarnitechConfig

from .LarnitechAirFan import LarnitechAirFan
from .LarnitechAirFanMultispeed import LarnitechAirFanMultispeed
from .LarnitechDevice import LarnitechDevice
from .LarnitechDeviceRegistry import LarnitechDeviceRegistry
from .LarnitechDeviceWrapper import LarnitechDeviceWrapper
from .LarnitechDimmerLamp import LarnitechDimmerLamp
from .LarnitechHumiditySensor import LarnitechHumiditySensor
from .LarnitechLamp import LarnitechLamp
from .LarnitechLeakSensor import LarnitechLeakSensor
from .LarnitechMotionSensor import LarnitechMotionSensor
from .LarnitechTemperatureSensor import LarnitechTemperatureSensor
from .LarnitechToggleable import LarnitechToggleable
from .LarnitechValve import LarnitechValve
from .LarnitechValveHeating import LarnitechValveHeating


LIB = {
    "temperature-sensor": LarnitechTemperatureSensor,
    "humidity-sensor": LarnitechHumiditySensor,
    "motion-sensor": LarnitechMotionSensor,
    "leak-sensor": LarnitechLeakSensor,
    "valve-heating": LarnitechValveHeating,
    # NOTE! the `LarnitechLamp` is not used intentionally
    # here as LT rather represents a switch, not a lamp.
    # It is actually a lamp when it comes to dimmable.
    "lamp": LarnitechToggleable,
    "dimmer-lamp": LarnitechDimmerLamp,
    "script": LarnitechToggleable,
    "valve": LarnitechValve,
    # Subtypes below.
    "air-fan": LarnitechAirFan,
}

WRAPPERS = (
    LarnitechAirFanMultispeed,
)


def _get_type(data: dict) -> str:
    sub_type = data.get("sub-type")

    # Use `sub-type` only it's explicitly registered.
    if sub_type and sub_type in LIB:
        return sub_type

    # Otherwise, try `type` and fallback to a generic.
    return data["type"]


def group(
    items: list[dict],
    client: LarnitechConfig,
) -> tuple[tuple[LarnitechDevice, ...], tuple[dict, ...]]:
    groups: dict[type[LarnitechDeviceWrapper], dict[str, list[LarnitechDevice]]] = {}
    to_ignore = []
    to_register = []

    for item in items:
        item_type = _get_type(item)

        if (
            item_type in client.ignored_types
            or item["addr"] in client.ignored_addrs
            or item["area"].lower() in client.ignored_areas
        ):
            to_ignore.append(item)
        else:
            device = LIB.get(item_type, LarnitechDevice)(item)

            if WRAPPERS:
                for wrapper in WRAPPERS:
                    if wrapper.wraps(device):
                        groups.setdefault(wrapper, {}).setdefault(device.area, []).append(device)
                    else:
                        to_register.append(device)
            else:
                to_register.append(device)

    for wrapper, devices_groups in groups.items():
        if len(devices_groups) == 1:
            for devices_group in devices_groups.values():
                to_register.append(devices_group)
        else:
            for devices_group in devices_groups.values():
                to_register.append(wrapper(devices_group))

    return tuple(to_register), tuple(to_ignore)


__all__ = [
    "LarnitechDeviceRegistry",
    "LarnitechDevice",
    "LarnitechDeviceWrapper",
    "group",
]
