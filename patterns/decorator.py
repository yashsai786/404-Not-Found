"""
==========================================
DESIGN PATTERN #7 — DECORATOR (Structural)
==========================================
Owner: Bhavika Sainani
Purpose:
  Optional hardware modules (Refrigeration, Solar, Network) are attached to a
  Kiosk dynamically without modifying the base Kiosk class. Each decorator
  wraps a KioskComponent and adds a capability + status string.
"""
from abc import ABC, abstractmethod


class KioskComponent(ABC):
    @abstractmethod
    def status(self) -> dict: ...
    @abstractmethod
    def capabilities(self) -> list: ...


class BaseKioskUnit(KioskComponent):
    """A bare kiosk hardware shell with no optional modules attached."""
    def __init__(self, kiosk_type):
        self.kiosk_type = kiosk_type

    def status(self):
        return {"base": f"{self.kiosk_type} kiosk online"}

    def capabilities(self):
        return ["dispense", "accept_payment"]


class ModuleDecorator(KioskComponent):
    def __init__(self, wrapped: KioskComponent):
        self._wrapped = wrapped

    def status(self):
        return self._wrapped.status()

    def capabilities(self):
        return list(self._wrapped.capabilities())


class RefrigerationModule(ModuleDecorator):
    def status(self):
        s = super().status(); s["refrigeration"] = "4°C nominal"; return s
    def capabilities(self):
        c = super().capabilities(); c.append("refrigeration"); return c


class SolarModule(ModuleDecorator):
    def status(self):
        s = super().status(); s["solar"] = "Generating 220W"; return s
    def capabilities(self):
        c = super().capabilities(); c.append("solar_power"); return c


class NetworkModule(ModuleDecorator):
    def status(self):
        s = super().status(); s["network"] = "Connected (5G)"; return s
    def capabilities(self):
        c = super().capabilities(); c.append("network"); return c


def build_kiosk_unit(kiosk_type, modules):
    """modules: list[str] in {'refrigeration','solar','network'}"""
    unit: KioskComponent = BaseKioskUnit(kiosk_type)
    mapping = {
        "refrigeration": RefrigerationModule,
        "solar": SolarModule,
        "network": NetworkModule,
    }
    for m in modules:
        cls = mapping.get(m.lower())
        if cls:
            unit = cls(unit)
    return unit
