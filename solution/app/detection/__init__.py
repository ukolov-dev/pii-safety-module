"""Deterministic PII detection public API (promoted v3.26)."""

from .detector_v3_26 import detect
from .models import DetectedEntity

__all__ = ["DetectedEntity", "detect"]
