from abc import ABC
from dataclasses import dataclass
from typing import Generic, TypeVar, TypeGuard

from .LarnitechDevice import LarnitechDevice
from ..utils import get_generic_args


_T = TypeVar("_T", bound=LarnitechDevice)


@dataclass(frozen=True, init=False)
class LarnitechDeviceWrapper(Generic[_T], LarnitechDevice, ABC):
    children: tuple[str, ...]
    """
    The list of `addr` this device wraps.
    """

    @classmethod
    def wraps(cls, device: LarnitechDevice) -> TypeGuard[_T]:
        model, = get_generic_args(cls, generic_position=0)
        assert issubclass(model, LarnitechDevice)
        return isinstance(device, model)

    def __init__(self, subs: list[_T]) -> None:
        combined_statuses = {}
        assert len(subs) > 1

        for sub in subs:
            assert self.wraps(sub)
            assert sub.area == subs[0].area
            assert sub.type == subs[0].type
            assert sub.extra.get("sub-type") == subs[0].extra.get("sub-type")
            combined_statuses[sub.addr] = sub.status

        handles = tuple(combined_statuses.keys())
        data = {
            "addr": ":".join(handles),
            "name": subs[0].name,
            "area": subs[0].area,
            "type": subs[0].type,
            "status": combined_statuses,
            "children": handles,
        }

        sub_type = subs[0].extra.get("sub-type")

        if sub_type:
            data["sub-type"] = sub_type

        super().__init__(data)

    def set_status(self, status: dict, addr: str) -> None:
        self.status[addr].update(status)


__all__ = [
    "LarnitechDeviceWrapper",
]
