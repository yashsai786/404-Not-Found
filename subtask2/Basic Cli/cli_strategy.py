from abc import ABC, abstractmethod

# Strategy Interface
class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount):
        pass

# Concrete Strategies
class UPIPayment(PaymentStrategy):
    def pay(self, amount):
        print(f"\n[UPI] Redirecting to UPI Intent... Payment of ${amount} Successful!")

class CardPayment(PaymentStrategy):
    def pay(self, amount):
        print(f"\n[CARD] Processing via Secure Gateway... Payment of ${amount} Successful!")

class CashPayment(PaymentStrategy):
    def pay(self, amount):
        print(f"\n[CASH] Please insert cash into the slot... ${amount} received. Payment Successful!")

# Context
class KioskCheckout:
    def __init__(self):
        self.items = {
            "1. Pizza": 12.0,
            "2. Burger": 8.0,
            "3. Coffee": 5.0,
            "4. Sandwich": 10.0
        }
        self.payment_strategy = None

    def set_payment_strategy(self, strategy: PaymentStrategy):
        self.payment_strategy = strategy

    def start_checkout(self):
        print("\n--- Strategy Design Pattern: Kiosk Checkout ---")
        for item, price in self.items.items():
            print(f"{item}: ${price}")
        
        try:
            choice = input("\nSelect item number to buy (or 'q' to quit): ")
            if choice.lower() == 'q': return False
            
            # Map selection to price
            item_list = list(self.items.values())
            selected_price = item_list[int(choice) - 1]
            print(f"Total Amount: ${selected_price}")
            
            print("\nSelect Payment Method:")
            print("1. UPI Payment")
            print("2. Credit/Debit Card")
            print("3. Cash at Terminal")
            
            pay_choice = input("Choice: ")
            
            match pay_choice:
                case "1":
                    self.set_payment_strategy(UPIPayment())
                case "2":
                    self.set_payment_strategy(CardPayment())
                case "3":
                    self.set_payment_strategy(CashPayment())
                case _:
                    print("Invalid Payment Method.")
                    return True
            
            # Execute the strategy
            if self.payment_strategy:
                self.payment_strategy.pay(selected_price)
            
        except (ValueError, IndexError):
            print("Invalid Selection.")
        
        return True

def main():
    checkout_system = KioskCheckout()
    running = True
    while running:
        running = checkout_system.start_checkout()

if __name__ == "__main__":
    main()
