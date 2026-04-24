"""
==========================================================
DESIGN PATTERN #2 — ABSTRACT FACTORY (Creational)
==========================================================
Owner: Megha Lalwani
Purpose:
  Each kiosk type needs a *family* of compatible components:
    - Dispenser   (Strategy implementations)
    - Payment Gateway default
    - Inventory policy tag
  Concrete factories: PharmacyFactory, FoodFactory, EmergencyFactory
"""
from abc import ABC, abstractmethod
from hardware.dispensers import SpiralDispenser, RoboticArmDispenser, ConveyorDispenser
from payments.gateways import CardAdapter, UPIAdapter, WalletAdapter


class KioskFactory(ABC):
    kiosk_type: str = "BASE"

    @abstractmethod
    def create_dispenser(self): ...

    @abstractmethod
    def create_default_payment(self): ...

    def inventory_policy(self) -> str:
        return "standard"


class PharmacyFactory(KioskFactory):
    kiosk_type = "PHARMACY"

    def create_dispenser(self):
        # robotic arm needed for precise medicine handling
        return RoboticArmDispenser()

    def create_default_payment(self):
        return CardAdapter()

    def inventory_policy(self):
        return "prescription_verified"


class FoodFactory(KioskFactory):
    kiosk_type = "FOOD"

    def create_dispenser(self):
        return SpiralDispenser()

    def create_default_payment(self):
        return UPIAdapter()

    def inventory_policy(self):
        return "expiry_tracked"


class EmergencyFactory(KioskFactory):
    kiosk_type = "EMERGENCY"

    def create_dispenser(self):
        return ConveyorDispenser()

    def create_default_payment(self):
        return WalletAdapter()  # often free, wallet just records distribution

    def inventory_policy(self):
        return "rationed"


def get_factory(kiosk_type: str) -> KioskFactory:
    mapping = {
        "PHARMACY": PharmacyFactory,
        "FOOD": FoodFactory,
        "EMERGENCY": EmergencyFactory,
    }
    if kiosk_type not in mapping:
        raise ValueError(f"Unknown kiosk type: {kiosk_type}")
    return mapping[kiosk_type]()
