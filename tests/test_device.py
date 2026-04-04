from lt2ha.device import group, LarnitechAirFan, LarnitechAirFanMultispeed


def _payload_airfan(addr: str, name: str, area: str) -> dict:
    return {
        "addr": addr,
        "type": "lamp",
        "name": name,
        "area": area,
        "sub-type": "air-fan",
        "status": {
            "auto-state": True,
            "state": "off",
        },
    }


def test_device_group(larnitech_config):
    devices = [
        _payload_airfan(addr="1:1", name="Fan Speed 1", area="Living Room"),
        _payload_airfan(addr="1:2", name="Fan Speed 2", area="Living Room"),
        _payload_airfan(addr="1:3", name="Airfan", area="Bathroom"),
        _payload_airfan(addr="1:4", name="Airfan", area="Toilet"),
        _payload_airfan(addr="1:5", name="Airfan", area="Bedroom"),
    ]
    to_register, to_ignore = group(items=devices, client=larnitech_config)

    assert len(to_register) == 4
    assert len(to_ignore) == 0
    assert isinstance(to_register[0], LarnitechAirFanMultispeed)
    # Assert addrs concat.
    assert to_register[0].addr == ":".join(to_register[0].children)
    # The first name is taken intentionally.
    assert to_register[0].name == devices[0]["name"]
    assert to_register[0].children == (devices[0]["addr"], devices[1]["addr"])
    assert to_register[0].status == {"1:1": devices[0]["status"], "1:2": devices[1]["status"]}

    assert isinstance(to_register[2], LarnitechAirFan)
    assert to_register[2].addr == devices[3]["addr"]

    assert isinstance(to_register[3], LarnitechAirFan)
    assert to_register[3].addr == devices[4]["addr"]
