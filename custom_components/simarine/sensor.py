"""Sensor setup for the Simarine integration."""

import logging

from homeassistant.components.sensor import (
  SensorDeviceClass,
  SensorEntity,
  SensorStateClass,
)
from homeassistant.const import (
  DEGREE,
  PERCENTAGE,
  UnitOfElectricCurrent,
  UnitOfElectricPotential,
  UnitOfPressure,
  UnitOfTemperature,
  UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

import simarine.types as simarinetypes

from . import SimarineConfigEntry
from .entity import SimarineEntity
from .coordinator import SimarineCoordinator


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
  hass: HomeAssistant,
  config_entry: SimarineConfigEntry,
  async_add_entities: AddEntitiesCallback,
):
  """Set up the Sensors."""
  coordinator: SimarineCoordinator = config_entry.runtime_data

  entities = []
  for sensor in coordinator.data.sensors.values():
    if isinstance(sensor, simarinetypes.NoneSensor):
      continue
    if coordinator.data.devices.get(sensor.device_id) is None:
      continue
    entities.append(SimarineSensorEntity(coordinator, sensor.id))

  async_add_entities(entities)


class SimarineSensorEntity(SimarineEntity, SensorEntity):
  """Implementation of a sensor."""

  def __init__(self, coordinator, sensor_id: str):
    super().__init__(coordinator, sensor_id)

    self._attr_state_class = SensorStateClass.MEASUREMENT if isinstance(self.sensor.state, (int, float)) else None
    self._attr_suggested_display_precision = 2 if isinstance(self.sensor.state, (int, float)) else None

    match type(self.sensor):
      case simarinetypes.AngleSensor:
        self._attr_native_unit_of_measurement = DEGREE
        self._attr_state_class = SensorStateClass.MEASUREMENT_ANGLE

      case simarinetypes.AtmosphereSensor:
        self._attr_device_class = SensorDeviceClass.ATMOSPHERIC_PRESSURE
        self._attr_native_unit_of_measurement = UnitOfPressure.MBAR

      case simarinetypes.AtmosphereTrendSensor:
        self._attr_native_unit_of_measurement = "mbar/h"

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

      case simarinetypes.RemainingTimeSensor:
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS

      # case simarinetypes.TimestampSensor:
      #  self._attr_device_class = SensorDeviceClass.TIMESTAMP
      #  self._attr_native_value = sensor.datetime
      #  self._attr_state_class = None

      case simarinetypes.VoltageSensor:
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT

  @property
  def native_value(self) -> int | float | str:
    return self.sensor.state
