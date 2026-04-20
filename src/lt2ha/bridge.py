import asyncio
import logging
from json import dumps as json_dumps, loads as json_loads, JSONDecodeError
from sys import stdout
from time import sleep
from typing import Any, Callable
from queue import Queue as ThreadSafeQueue

from json_repair import repair_json
from paho.mqtt.client import MQTTMessage, MQTTProtocolVersion
from websockets import (
    ClientConnection as WsClientConnection,
    ConnectionClosedError as WsConnectionClosedError,
)

from .device import LarnitechDevice, LarnitechDeviceRegistry, LarnitechDeviceWrapper, group
from .mqtt import Mqtt, MqttClient, MqttDiscovery
from .LarnitechConfig import LarnitechConfig
from .utils import build_topic, to_id


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
_LOGGER.addHandler(logging.StreamHandler(stdout))


_PREFIX = "larnitech"


class LarnitechMqttBridge:
    def __init__(
        self,
        mqtt: Mqtt,
        larnitech: LarnitechConfig,
    ):
        self._mqtt = mqtt
        self._larnitech = larnitech
        self._devices = LarnitechDeviceRegistry()
        self._ws: WsClientConnection | None = None
        self._status_set_queue = ThreadSafeQueue[tuple[str, dict]]()
        self._mqtt.client.on_message = self._notify_lt

    def _register_device(self, device: LarnitechDevice) -> None:
        """
        Register a Larnitech device based on its config.
        """
        addr_id = to_id(device.addr)
        area_id = to_id(device.area)
        unique_id = f"{_PREFIX}_{addr_id}"
        topic_prefix = f"{_PREFIX}/{addr_id}"

        for key, value in device.config.items():
            if key.endswith("command_topic"):
                assert isinstance(value, str), key
                device.config[key] = build_topic(topic_prefix, value, "set")
                # Auto-subscribe to the commands.
                self._mqtt.client.subscribe(device.config[key])
            elif key.endswith("_topic"):
                assert isinstance(value, str), key
                device.config[key] = build_topic(topic_prefix, value, "state")

        device.config.update({
            "area": device.area,
            "name": f"{device.area} {device.name}",
            "unique_id": unique_id,
            "default_entity_id": f"{_PREFIX}_{area_id}_{to_id(device.name)}",
            "device": {
                "name": "Larnitech",
                "model": "Metaforsa 3.plus",
                "identifiers": [f"mf14_3plus_{area_id}"],
                "suggested_area": device.area,
            },
        })

        # Tell HA about the new device.
        self._mqtt.client.publish(
            f"{self._mqtt.discovery.prefix}/{device.entity_type}/{unique_id}/config",
            device.config,
            retain=True,
        )

        # Store for further operations.
        self._devices.add(device)

    def _notify_ha(self, device: LarnitechDevice) -> None:
        for topic_key, payload in device.notify_ha().items():
            assert topic_key.endswith("_topic") and not topic_key.endswith("command_topic")
            self._mqtt.client.publish(device.config[topic_key], payload)

    def _notify_lt(self, message: MQTTMessage) -> None:
        if self._ws and message.topic.startswith(f"{_PREFIX}/") and message.topic.endswith("/set"):
            # Drop `_PREFIX` from the start and `set` from the end.
            path = message.topic.split("/")[1:-1]
            addr = path.pop(0).replace("_", ":")
            device = self._devices.get(addr)

            if device:
                # noinspection PyUnresolvedReferences
                status = device.notify_lt(
                    path.pop(0) if path else None,
                    message.payload.decode(),
                )

                # Make a list of updates.
                if isinstance(status, dict):
                    status = ((addr, status),)

                # Queue updates.
                for _addr, _status in status:
                    self._status_set_queue.put((_addr, _status))

    async def _process_status_set_queue(self):
        while True:
            await asyncio.sleep(0.01)

            while not self._status_set_queue.empty():
                _addr, _status = self._status_set_queue.get_nowait()

                await self._ws_send(
                    request="status-set",
                    status=_status,
                    addr=_addr,
                )

    async def run(self):
        self._mqtt.client.loop_start()
        _LOGGER.info("MQTT client connected")

        status_set_task: asyncio.Task | None = None

        try:
            async with self._larnitech.connect() as self._ws:
                _LOGGER.info("LT connection established")

                await self._ws_send(
                    request="authorize",
                    handler=self._lt_on_auth,
                    key=self._larnitech.key,
                )
                await self._ws_send(
                    request="get-devices",
                    handler=self._lt_on_get_devices,
                    status="detailed",
                )
                await self._ws_send(
                    request="status-subscribe",
                    handler=self._lt_on_status_subscribe,
                    addr=tuple([
                        addr
                        for children
                        in [
                            device.children
                            if isinstance(device, LarnitechDeviceWrapper)
                            else (device.addr,)
                            for device
                            in self._devices
                        ]
                        for addr
                        in children
                    ]),
                )

                # Deliver status updates to LT in a separate thread.
                status_set_task = asyncio.create_task(self._process_status_set_queue())

                while True:
                    message = await self._ws_receive()

                    if message.get("response") == "status-set":
                        self._lt_on_status_set(**message)
                    elif message.get("event") == "statuses":
                        self._lt_on_status_update(**message)
                    else:
                        _LOGGER.warning(f"⚠️ Unexpected message {message}")
        finally:
            if status_set_task:
                status_set_task.cancel()
                _LOGGER.info("Cancelled the LT updates task")

            self._mqtt.client.disconnect()
            self._mqtt.client.loop_stop()
            _LOGGER.info("MQTT client disconnected")

    def run_sync(
        self,
        restart_attempts: int = 5,
        # It's better to wait longer on LT (re)start because the system start and
        # entities readiness are separate topics. The latter takes notably longer.
        restart_delay: float = 5,
    ) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bridge = loop.create_task(self.run())

        try:
            loop.run_until_complete(bridge)
        except WsConnectionClosedError as lt_connection_error:
            status = "LT connection lost"

            _LOGGER.info(status)

            if not bridge.cancelled() and not bridge.cancelling():
                bridge.cancel(status)

            # Error immediately since no reties allowed.
            if restart_attempts <= 0:
                raise lt_connection_error

            try:
                _LOGGER.info(f"Retrying in {restart_delay} seconds")
                sleep(restart_delay)
                self.run_sync(
                    restart_attempts=restart_attempts,
                    restart_delay=restart_delay,
                )
            except Exception as bridge_restart_error:
                if restart_attempts <= 0:
                    raise bridge_restart_error
                else:
                    restart_attempts -= 1
                    _LOGGER.info(f"Retry attempt failed, {restart_attempts} left")
                    self.run_sync(
                        restart_attempts=restart_attempts,
                        restart_delay=restart_delay,
                    )
        except KeyboardInterrupt:
            bridge.cancel()
            _LOGGER.info("Bye 👋🏻")

    @staticmethod
    async def _lt_on_auth(result: str, **_: dict) -> None:
        if result == "success":
            _LOGGER.info("✅ LT: Authorized")
        else:
            _LOGGER.error("🚫 LT: Auth failed")
            raise RuntimeError()

    async def _lt_on_get_devices(
        self,
        devices: list[dict],
        found: int,
        **_: dict,
    ) -> None:
        to_register, to_ignore = group(
            items=devices,
            client=self._larnitech,
        )

        for device in to_register:
            self._register_device(device)

        for item in to_ignore:
            _LOGGER.info(f"🚫 LT: Ignoring {item}")

        # Give the devices time to register.
        await asyncio.sleep(3)

        # Set the initial state.
        for device in self._devices:
            self._notify_ha(device)

        # Some devices in HA may absorb several devices from LT so
        # the sum of ignored and registered might not match the total.
        _LOGGER.info(
            (
                f"✅ LT: {found} devices: "
                f"{len(to_ignore)} ignored, "
                f"{len(self._devices)} registered"
            ),
        )

    @staticmethod
    async def _lt_on_status_subscribe(
        found: int,
        subscribed: int,
        devices: list[dict],
        addr: tuple[str, ...],
        **_: dict,
    ) -> None:
        size = len(addr)
        assert devices
        assert size == found
        assert size == subscribed
        if found == subscribed:
            _LOGGER.info(f"✅ LT: Subscribed to {size} devices.")
        else:
            _LOGGER.error(f"😰 LT: Subscribed to {subscribed} out of {size} devices.")
            raise RuntimeError()

    def _lt_on_status_set(self, devices: list[dict], **_: dict) -> None:
        for item in devices:
            device = self._devices.get(item["addr"])

            if item["success"]:
                _LOGGER.debug(f"✅ LT: Status changed for {device.name} in {device.area}.")
            else:
                _LOGGER.error(
                    (
                        "😰 LT: Failed to change status for "
                        f"{device.name} in {device.area}. {item}"
                    ),
                )

    def _lt_on_status_update(self, devices: list[dict], **_: dict) -> None:
        for item in devices:
            device = self._devices.get(item["addr"])

            if device:
                device.set_status(item["status"], item["addr"])
                # _LOGGER.debug(
                #     (
                #         f"⬅️ LT: Received {device.status} "
                #         f"({device.area} / {device.name})"
                #     ),
                # )
                self._notify_ha(device)

    async def _ws_receive(self) -> dict:
        frame = await self._ws.recv(decode=False)
        message = (
            frame.decode("utf-8", errors="ignore")
            if isinstance(frame, bytes)
            else frame
        )

        try:
            return json_loads(message, strict=False)
        except JSONDecodeError:
            _LOGGER.error(f"LT: Malformed JSON: {message}")
            return repair_json(message, skip_json_loads=True, return_objects=True)

    async def _ws_send(
        self,
        request: str,
        handler: Callable | None = None,
        **kwargs: Any,
    ) -> None:
        message = {"request": request, **kwargs}
        device = self._devices.get(kwargs.get("addr", ""))

        if device:
            assert isinstance(device, LarnitechDevice)
            _LOGGER.debug(f"➡️ LT: Sending {message} ({device.area} / {device.name})")
        else:
            _LOGGER.debug(f"➡️ LT: Sending {message}")

        await self._ws.send(json_dumps(message))

        if handler:
            response = await self._ws_receive()
            assert response["response"] == request
            await handler(**response, **kwargs)


def main() -> None:
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "mqtt_client_id",
    )
    parser.add_argument(
        "--ha-mqtt-discovery-prefix",
        required=True,
    )
    parser.add_argument(
        "--mqtt-host",
        required=True,
    )
    parser.add_argument(
        "--mqtt-port",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--mqtt-username",
        required=True,
    )
    parser.add_argument(
        "--mqtt-password",
        required=True,
    )
    parser.add_argument(
        "--mqtt-proto",
        type=int,
        required=True,
        choices=[c.value for c in MQTTProtocolVersion],
    )
    parser.add_argument(
        "--mqtt-transport",
        required=True,
        choices=["tcp", "websockets", "unix"],
    )
    parser.add_argument(
        "--lt-host",
        required=True,
    )
    parser.add_argument(
        "--lt-port",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--lt-key",
        required=True,
    )
    parser.add_argument(
        "--lt-ignore-addr",
        default=[],
        metavar="DEVICE_ADDR",
        nargs="+",
        dest="ignored_addrs",
    )
    parser.add_argument(
        "--lt-ignore-type",
        default=[],
        metavar="DEVICE_TYPE",
        nargs="+",
        dest="ignored_types",
    )
    parser.add_argument(
        "--lt-ignore-area",
        default=[],
        metavar="AREA_NAME",
        nargs="+",
        dest="ignored_areas",
    )
    parser.add_argument(
        "--restart-attempts",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--restart-delay",
        type=int,
        default=5,
    )

    args = parser.parse_args()
    bridge = LarnitechMqttBridge(
        mqtt=Mqtt(
            client=MqttClient(
                client_id=args.mqtt_client_id,
                host=args.mqtt_host,
                port=args.mqtt_port,
                username=args.mqtt_username,
                password=args.mqtt_password,
                protocol=MQTTProtocolVersion(args.mqtt_proto),
                transport=args.mqtt_transport,
            ),
            discovery=MqttDiscovery(
                prefix=args.ha_mqtt_discovery_prefix,
            ),
        ),
        larnitech=LarnitechConfig(
            host=args.lt_host,
            port=args.lt_port,
            key=args.lt_key,
            ignored_addrs=tuple(args.ignored_addrs),
            ignored_types=tuple(args.ignored_types),
            ignored_areas=tuple(args.ignored_areas),
        ),
    )

    bridge.run_sync(
        restart_attempts=args.restart_attempts,
        restart_delay=args.restart_delay,
    )


if __name__ == "__main__":
    main()
