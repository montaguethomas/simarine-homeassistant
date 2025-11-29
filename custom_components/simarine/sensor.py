from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import (
  DEGREE,
  PERCENTAGE,
  UnitOfElectricCurrent,
  UnitOfElectricPotential,
  UnitOfPressure,
  UnitOfTemperature,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

import simarine.types as simarinetypes

from .const import DOMAIN


class SimarineSensor(CoordinatorEntity, SensorEntity):
  def __init__(self, coordinator, sensor_id: str):
    super().__init__(coordinator)

    sensor = self.coordinator.data["sensors"].get(sensor_id)
    device = self.coordinator.data["devices"].get(sensor.device_id)

    system_info = self.coordinator.data.get("system_info", {})
    serial_number = system_info.get("serial_number")
    firmware_version = system_info.get("firmware_version")

    self._attr_device_info = DeviceInfo(
      default_name=f"Simarine {serial_number}",
      identifiers={(DOMAIN, serial_number)},
      manufacturer="Simarine",
      model="Pico",
      serial_number=serial_number,
      sw_version=firmware_version,
    )
    self._attr_unique_id = f"{serial_number}-{sensor_id}"
    self._attr_name = f"{device.name or device.type} {sensor.type}"

    self._attr_native_value = sensor.state
    self._attr_state_class = SensorStateClass.MEASUREMENT
    self._attr_suggested_display_precision = 2

    match type(sensor):
      case simarinetypes.AngleSensor:
        self._attr_native_unit_of_measurement = DEGREE
        self._attr_state_class = SensorStateClass.MEASUREMENT_ANGLE

      case simarinetypes.AtmosphereSensor:
        self._attr_device_class = SensorDeviceClass.ATMOSPHERIC_PRESSURE
        self._attr_native_unit_of_measurement = UnitOfPressure.MBAR

      case simarinetypes.AtmosphereTrendSensor:
        self._attr_native_unit_of_measurement = "mb/h"

      case simarinetypes.CoulombCounterSensor:
        self._attr_native_unit_of_measurement = "Ah"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

      case simarinetypes.CurrentSensor:
        self._attr_device_class = SensorDeviceClass.CURRENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

      # case simarinetypes.ResistanceSensor:
      #  self._attr_device_class = SensorDeviceClass.

      case simarinetypes.StateOfChargeSensor:
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE

      case simarinetypes.TemperatureSensor:
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

      case simarinetypes.TimestampSensor:
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_native_value = sensor.datetime

      case simarinetypes.VoltageSensor:
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT


async def async_setup_entry(hass, config_entry, async_add_entities):
  coordinator = hass.data[DOMAIN][config_entry.entry_id]

  entities = []
  for sensor in coordinator.data["sensors"]:
    if type(sensor) is simarinetypes.NoneSensor:
      continue
    if coordinator.data["devices"].get(sensor.device_id) is None:
      continue
    entities.append(SimarineSensor(coordinator, sensor.id))

  async_add_entities(entities)
