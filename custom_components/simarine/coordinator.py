from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

from simarine.client import SimarineClient


_LOGGER = logging.getLogger(__name__)


class SimarineCoordinator(DataUpdateCoordinator):
  def __init__(self, hass: HomeAssistant, host, tcp_port, udp_port, update_interval: int):
    self._hass = hass

    self.host = host
    self.tcp_port = tcp_port
    self.udp_port = udp_port
    self.update_interval_seconds = update_interval

    self._client = None
    self._connected = False

    self._system_info = None
    self._system_device = None
    self._devices = None
    self._sensors = None

    super().__init__(
      hass,
      _LOGGER,
      name="Simarine",
      update_interval=timedelta(seconds=update_interval),
    )

  def _connect(self):
    try:
      if self.host:
        _LOGGER.info("Connecting to Simarine @ %s (TCP:%s UDP:%s)", self.host, self.tcp_port, self.udp_port)
      else:
        _LOGGER.info("Auto-discovering Simarine device...")

      self._client = SimarineClient(
        tcp_kwargs={"host": self.host, "port": self.tcp_port},
        udp_kwargs={"port": self.udp_port},
      )
      self._client.open()
      self._connected = True
      _LOGGER.info("Connected to Simarine")

    except Exception as e:
      self._client = None
      self._connected = False
      _LOGGER.warning("Simarine connection failed: %s", e)

  def _disconnect(self):
    if self._client:
      try:
        self._client.close()
      except Exception:
        pass
    self._client = None
    self._connected = False

  async def _async_update_data(self):
    try:
      if not self._connected or not self._client:
        self._connect()

      if not self._connected:
        raise UpdateFailed("Unable to connect to Simarine device")

      if self._system_info is None:
        self._system_info = dict(zip(["serial_number", "firmware_version"], self._client.get_system_info()))

      if self._system_device is None:
        self._system_device = self.client.get_system_device()

      if self._devices is None:
        self._devices = self._client.get_devices()

      if self._sensors is None:
        self._sensors = self._client.get_sensors()
        self._client.update_sensors_state(self._sensors)
      else:
        sensors_state = self._client.get_sensors_state()
        for id, state_field in sensors_state.items():
          if id in self._sensors:
            self._sensors[id].state_field = state_field
          else:
            self._sensors[id] = self._client.get_sensor(id)
            if self._sensors[id].device_id not in self._devices:
              self._devices[id] = self._client.get_device(id)

      return {
        "system_info": self._system_info,
        "system_device": self._system_device,
        "devices": self._devices,
        "sensors": self._sensors,
      }

    except Exception as e:
      _LOGGER.warning("Simarine update failed: %s", e)
      self._disconnect()
      raise UpdateFailed(f"Simarine connection lost: {e}")
