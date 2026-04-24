"""
========================================
DESIGN PATTERN #3 — STRATEGY (Behavioral)
========================================
Owners: Harshil Dodwani / Bhavika Sainani
Purpose:
  Two strategy families:
    (a) Dispenser strategies (hardware behaviour)  — see hardware/dispensers.py
    (b) Pricing strategies (runtime price computation) — defined here.

Pricing strategies are interchangeable at runtime via the registry's
'emergency_mode' config flag.
"""
from abc import ABC, abstractmethod


class PricingStrategy(ABC):
    name = "base"

    @abstractmethod
    def compute(self, item) -> float: ...


class StandardPricing(PricingStrategy):
    name = "standard"

    def compute(self, item):
        return round(item.price, 2)


class DiscountedPricing(PricingStrategy):
    name = "discounted"
    rate = 0.15

    def compute(self, item):
        return round(item.price * (1 - self.rate), 2)


class EmergencyPricing(PricingStrategy):
    """During emergencies, essentials use the custom emergency price."""
    name = "emergency"

    def compute(self, item):
        return round(item.emergency_price, 2)


def select_pricing(emergency: bool, discount: bool = False) -> PricingStrategy:
    if emergency:
        return EmergencyPricing()
    if discount:
        return DiscountedPricing()
    return StandardPricing()
