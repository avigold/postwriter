"""Literary device detection, annotation, and analysis."""

from postwriter.devices.taxonomy import DeviceInstance as DeviceInstanceData
from postwriter.devices.annotation import DeviceAnnotator

__all__ = ["DeviceAnnotator", "DeviceInstanceData"]
