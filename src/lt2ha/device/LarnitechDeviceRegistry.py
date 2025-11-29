from typing import Generator

from .LarnitechDevice import LarnitechDevice
from .LarnitechDeviceWrapper import LarnitechDeviceWrapper


class LarnitechDeviceRegistry:
    def __init__(self) -> None:
        self._registry = {}
        self._aliases = {}

    def add(self, device: LarnitechDevice) -> None:
        self._registry[device.addr] = device

        if isinstance(device, LarnitechDeviceWrapper):
            for addr in device.children:
                self._aliases[addr] = device.addr

    def get(self, addr: str) -> LarnitechDevice | None:
        alias = self._aliases.get(addr, addr)

        return self._registry.get(alias)

    def __iter__(self) -> Generator[LarnitechDevice, None, None]:
        for device in self._registry.values():
            yield device

    def __len__(self) -> int:
        return len(self._registry)


__all__ = [
    "LarnitechDeviceRegistry",
]
