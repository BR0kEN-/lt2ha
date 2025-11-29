from json import dumps as json_dumps
from typing import Any, Callable, Literal, Self

from paho.mqtt.client import (
    CallbackAPIVersion,
    Client,
    MQTTMessage,
    MQTTMessageInfo,
    MQTTProtocolVersion,
    PayloadType,
)
from paho.mqtt.properties import Properties


class MqttClient(Client):
    def __init__(
        self,
        client_id: str,
        host: str,
        port: int,
        username: str,
        password: str,
        protocol: MQTTProtocolVersion,
        transport: Literal["tcp", "websockets", "unix"],
    ) -> None:
        super().__init__(
            protocol=protocol,
            transport=transport,
            client_id=client_id,
            callback_api_version=CallbackAPIVersion.VERSION2,
        )

        self.username_pw_set(username, password)
        self.connect(host, port)

    @Client.on_message.setter
    def on_message(self, func: Callable[[MQTTMessage], None] | None) -> None:
        def wrapper(_: Self, __: Any, message: MQTTMessage) -> None:
            func(message)

        Client.on_message.fset(self, wrapper)

    def publish(
        self,
        topic: str,
        payload: PayloadType | dict = None,
        qos: int = 0,
        retain: bool = False,
        properties: Properties | None = None,
    ) -> MQTTMessageInfo:
        return super().publish(
            topic,
            json_dumps(payload) if isinstance(payload, dict) else payload,
            qos=qos,
            retain=retain,
            properties=properties,
        )


__all__ = [
    "MqttClient",
]
