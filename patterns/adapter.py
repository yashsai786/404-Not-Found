"""
=========================================
DESIGN PATTERN #4 — ADAPTER (Structural)
=========================================
Owner: Harshil Dodwani
Purpose:
  Different payment vendors expose incompatible APIs. Adapters wrap them and
  expose a single unified IPaymentGateway interface (.pay(amount)).
"""
from abc import ABC, abstractmethod


# ---- Common target interface ----
class IPaymentGateway(ABC):
    name = "base"

    @abstractmethod
    def pay(self, amount: float) -> dict: ...


# ---- Adaptee #1: Bank's old card SDK ----
class _LegacyCardSDK:
    def charge_credit_card(self, dollars):
        return {"ref": f"CC-{int(dollars*100)}", "ok": True}


class CardAdapter(IPaymentGateway):
    name = "Card"

    def __init__(self):
        self._sdk = _LegacyCardSDK()

    def pay(self, amount):
        r = self._sdk.charge_credit_card(amount)
        return {"provider": "Card", "ref": r["ref"], "amount": amount, "ok": r["ok"]}


# ---- Adaptee #2: UPI service with totally different signature ----
class _UPIService:
    def send_payment_request(self, payee_vpa, amount_in_paise):
        return {"txn_id": f"UPI-{amount_in_paise}", "status": "SUCCESS"}


class UPIAdapter(IPaymentGateway):
    name = "UPI"

    def __init__(self, vpa="aurakiosk@upi"):
        self._svc = _UPIService()
        self._vpa = vpa

    def pay(self, amount):
        r = self._svc.send_payment_request(self._vpa, int(amount * 100))
        return {
            "provider": "UPI",
            "ref": r["txn_id"],
            "amount": amount,
            "ok": r["status"] == "SUCCESS",
        }


# ---- Adaptee #3: digital wallet ----
class _WalletAPI:
    def debit(self, user, value):
        return {"id": f"W-{value}", "approved": True}


class WalletAdapter(IPaymentGateway):
    name = "Wallet"

    def __init__(self, user="anonymous"):
        self._api = _WalletAPI()
        self._user = user

    def pay(self, amount):
        r = self._api.debit(self._user, amount)
        return {"provider": "Wallet", "ref": r["id"], "amount": amount, "ok": r["approved"]}
