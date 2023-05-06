"""Properties a device might have."""
from .binary_sensor_property import BinarySensorProperty
from .binary_switch_property import BinarySwitchProperty
from .consumption_property import ConsumptionProperty
from .humidity_bar_property import HumidityBarProperty
from .multi_level_sensor_property import MultiLevelSensorProperty
from .multi_level_switch_property import MultiLevelSwitchProperty
from .remote_control_property import RemoteControlProperty
from .settings_property import SettingsProperty

__all__ = [
    "BinarySensorProperty",
    "BinarySwitchProperty",
    "ConsumptionProperty",
    "HumidityBarProperty",
    "MultiLevelSensorProperty",
    "MultiLevelSwitchProperty",
    "RemoteControlProperty",
    "SettingsProperty",
]
