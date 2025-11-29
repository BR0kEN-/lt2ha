from dataclasses import dataclass

from .MqttClient import MqttClient
from .MqttDiscovery import MqttDiscovery


@dataclass(frozen=True)
class Mqtt:
    client: MqttClient
    discovery: MqttDiscovery


__all__ = [
    "Mqtt",
    "MqttClient",
    "MqttDiscovery",
]
