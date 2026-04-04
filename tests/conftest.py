import pytest

from lt2ha.LarnitechConfig import LarnitechConfig


@pytest.fixture
def larnitech_config() -> LarnitechConfig:
    return LarnitechConfig(
        host="localhost",
        port=1,
        key="i-am-a-key",
        ignored_addrs=(),
        ignored_areas=(),
        ignored_types=(),
    )
