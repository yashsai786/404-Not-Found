"""
==========================================
DESIGN PATTERN #5 — COMPOSITE (Structural)
==========================================
Owner: Yash Gangwani
Purpose:
  Inventory contains both individual Products AND Bundles (which may nest other
  bundles). A common Item interface lets clients treat both uniformly.
"""
from abc import ABC, abstractmethod
from patterns.strategy import select_pricing
from patterns.singleton import CentralRegistry

class Item(ABC):
    @abstractmethod
    def get_price(self) -> float: ...
    @abstractmethod
    def is_available(self, qty: int = 1) -> bool: ...
    @abstractmethod
    def describe(self) -> dict: ...
    @property
    @abstractmethod
    def requires_refrigeration(self) -> bool: ...
    @property
    @abstractmethod
    def stock(self) -> int: ...


class Product(Item):
    def __init__(self, pid, name, price, stock, refr=False, emergency_price=0.0):
        self.id = pid
        self.name = name
        self.price = price
        self.emergency_price = emergency_price
        self._stock = int(stock)
        self._refr = bool(refr)

    @property
    def stock(self):
        return self._stock

    @stock.setter
    def stock(self, val):
        self._stock = int(val)

    @property
    def requires_refrigeration(self):
        return self._refr

    def get_price(self):
        # DESIGN PATTERN: Strategy
        # Use the global state to decide which pricing strategy to apply
        registry = CentralRegistry()
        is_emergency = registry.get_config("emergency_mode") == "1"
        strategy = select_pricing(is_emergency)
        return strategy.compute(self)

    def is_available(self, qty=1):
        return self.stock >= qty

    def describe(self):
        return {
            "type": "product",
            "id": self.id,
            "name": self.name,
            "price": self.get_price(), # returns active price based on strategy
            "base_price": self.price,
            "emergency_price": self.emergency_price,
            "stock": self.stock,
            "requires_refrigeration": self.requires_refrigeration,
        }


class Bundle(Item):
    def __init__(self, bid, name, price=0.0, emergency_price=0.0):
        self.id = bid
        self.name = name
        self._price = price
        self._emergency_price = emergency_price
        self.children = []      # list of (Item, qty)

    def add(self, item: Item, qty: int = 1):
        self.children.append((item, qty))

    @property
    def price(self):
        """Standard price fallback to total sum of children."""
        if self._price > 0:
            return self._price
        return round(sum(child.price * q for child, q in self.children), 2)

    @property
    def emergency_price(self):
        """Emergency price fallback to 10% discount on total sum."""
        if self._emergency_price > 0:
            return self._emergency_price
        return round(self.price * 0.9, 2)

    def get_price(self):
        # DESIGN PATTERN: Strategy
        registry = CentralRegistry()
        is_emergency = registry.get_config("emergency_mode") == "1"
        strategy = select_pricing(is_emergency)
        return strategy.compute(self)

    def is_available(self, qty=1):
        return all(child.is_available(q * qty) for child, q in self.children)

    def describe(self):
        return {
            "type": "bundle",
            "id": self.id,
            "name": self.name,
            "price": self.get_price(),
            "base_price": self._price, # show the ACTUAL custom price in UI edit
            "emergency_price": self._emergency_price,
            "available": self.is_available(),
            "children": [
                {"qty": q, **child.describe()} for child, q in self.children
            ],
        }

    @property
    def requires_refrigeration(self):
        return any(child.requires_refrigeration for child, q in self.children)

    @property
    def stock(self):
        if not self.children: return 0
        return min(child.stock // q for child, q in self.children)
