# Larnitech to Home Assistant Bridge

This software lets you forget about the Larnitech app and transfer your smart home Larnitech controls to Home Assistant, unifying everything in a single place.

The supported device types can be found [here](src/lt2ha/device/__init__.py).

> [!TIP]
> - It is crucial to correctly set device's subtype in the Larnitech app. I.e. a `script` that controls the air fan must be set to `air-fan`.
> - Ensure areas in Larnitech and Home Assistant are named the same. Otherwise, areas with the Larnitech's names will be automatically added to HA potentially causing duplication.

## Requirements

### Hardware

- Any Larnitech hub with the [API2](https://wiki.larnitech.com/API2) support.
- Any device or a set of devices capable to host the MQTT broker and the bridge.

### Software

- Python >= 3.13

## Installation

```bash
git clone git@github.com:BR0kEN-/lt2ha.git
cd lt2ha
pip3 install -e .
```

## Usage

The bridge must be always up. It receives events over Websockets from Larnitech and delivers updates to Home Assistant over an MQTT.

```bash
lt2ha-bridge \
  larnitech-bridge \
  --ha-mqtt-discovery-prefix homeassistant \
  --mqtt-host 127.0.0.1 \
  --mqtt-port 1883 \
  --mqtt-username 'jondoe' \
  --mqtt-password 'heyiampassw0rd' \
  --mqtt-proto 4 \
  --mqtt-transport tcp \
  --lt-host 192.168.68.55 \
  --lt-port 2041 \
  --lt-key 'heyiamanapikey' \
  --lt-ignore-area Setup \
  --lt-ignore-type com-port
```

> [!TIP]
> It is suggested to restart the process after the Home Assistant and/or MQTT broker is (re)booted.

> [!CAUTION]
> The Larnitech API key prints to the log output as is.

### How do you run it?

This project runs on a Raspberry Pi 5 that also hosts a Home Assistant Supervised installation (now deprecated, so I'm not encouraging its use). Since I maintain full control over the underlying operating system (Debian Bookworm), the HA-to-Larnitech bridge is deployed as a systemd service, alongside several other system-level components managed in a similar manner.

Find `*.service` file below:

```ini
[Unit]
Description=Larnitech Bridge
After=network.target

[Service]
ExecStart=lt2ha-bridge larnitech-bridge --ha-mqtt-discovery-prefix homeassistant --mqtt-host 127.0.0.1 --mqtt-port 1883 --mqtt-username 'mosquitto' --mqtt-password 'heyiampassw0rd' --mqtt-proto 4 --mqtt-transport tcp --lt-host 192.168.68.55 --lt-port 2041 --lt-key 'heyiamanapikey' --lt-ignore-area Setup --lt-ignore-type com-port
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### Screenshots

![Overview](docs/images/1-overview.jpg)
![Devices](docs/images/2-devices.jpg)
![Devices](docs/images/3-devices.jpg)
![Devices](docs/images/4-devices.jpg)

## Disclaimer

This software is provided as is without any express or implied warranties. The author is not responsible for any damage or data loss. Use at your own risk.
