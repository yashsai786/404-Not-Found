"""
Strategy Pattern — Dispenser hardware family.
Each concrete dispenser is interchangeable at runtime through IDispenser.
"""
from abc import ABC, abstractmethod
import time


class IDispenser(ABC):
    name = "base"

    @abstractmethod
    def dispense(self, item_name: str) -> str: ...


class SpiralDispenser(IDispenser):
    name = "Spiral"
    def dispense(self, item_name):
        time.sleep(0.05)
        return f"[Spiral] Rotated coil to release {item_name}"


class RoboticArmDispenser(IDispenser):
    name = "Robotic Arm"
    def dispense(self, item_name):
        time.sleep(0.05)
        return f"[Robotic Arm] Picked & placed {item_name} into tray"


class ConveyorDispenser(IDispenser):
    name = "Conveyor"
    def dispense(self, item_name):
        time.sleep(0.05)
        return f"[Conveyor] Belt delivered {item_name} to user"


def get_dispenser(name: str) -> IDispenser:
    return {
        "spiral": SpiralDispenser(),
        "robotic": RoboticArmDispenser(),
        "conveyor": ConveyorDispenser(),
    }.get(name.lower(), SpiralDispenser())
