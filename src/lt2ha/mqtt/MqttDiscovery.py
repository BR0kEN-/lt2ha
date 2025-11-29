from dataclasses import dataclass


@dataclass(frozen=True)
class MqttDiscovery:
    prefix: str


__all__ = [
    "MqttDiscovery",
]
