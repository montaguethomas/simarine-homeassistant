"""Base entity for the Simarine integration."""

import logging

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

import simarine.types as simarinetypes

from .const import DOMAIN
from .coordinator import SimarineCoordinator


_LOGGER = logging.getLogger(__name__)


class SimarineEntity(CoordinatorEntity[SimarineCoordinator]):
  """Simarine entity."""

  _attr_has_entity_name = True

  def __init__(self, coordinator: SimarineCoordinator, sensor_id: int) -> None:
    """Initialise entity."""
    super().__init__(coordinator)
    self.sensor_id = sensor_id

  @property
  def sensor(self) -> simarinetypes.Sensor:
    return self.coordinator.data.sensors.get(self.sensor_id)

  @property
  def device(self) -> simarinetypes.Device:
    if self.sensor is None:
      return None
    return self.coordinator.data.devices.get(self.sensor.device_id)

  @property
  def device_info(self) -> DeviceInfo:
    """Return device information."""
    return DeviceInfo(
      identifiers={(DOMAIN, self.coordinator.data.serial_number)},
      manufacturer="Simarine",
      model="Pico",  # static for now
      name=f"Simarine Pico {self.coordinator.data.serial_number}",
      serial_number=self.coordinator.data.serial_number,
      sw_version=self.coordinator.data.firmware_version,
    )

  @property
  def name(self) -> str:
    """Return the name of the sensor."""
    return f"{self.device.name or self.device.title} {self.sensor.title}"

  @property
  def unique_id(self) -> str:
    """Return unique id."""
    return f"{DOMAIN}-{self.coordinator.data.serial_number}-{self.device.type}-{self.device.id}-{self.sensor.type}-{self.sensor.id}"
