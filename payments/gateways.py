"""
Adapter Pattern — wraps incompatible vendor SDKs into one interface.
This module now imports implementations from the patterns/ directory.
"""
from patterns.adapter import IPaymentGateway, CardAdapter, UPIAdapter, WalletAdapter


def get_gateway(name: str) -> IPaymentGateway:
    return {"card": CardAdapter(), "upi": UPIAdapter(), "wallet": WalletAdapter()}.get(
        name.lower(), CardAdapter()
    )
