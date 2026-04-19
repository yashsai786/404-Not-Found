class KioskInterface:
    def dispense_item(self, item):
        pass
    def view_financial_reports(self):
        pass

class RealKiosk(KioskInterface):
    def __init__(self):
        self.inventory = {"Pizza": 10, "Burger": 5, "Coke": 20}
        self.sales_total = 1250.50 # Sensitive data

    def dispense_item(self, item):
        if item in self.inventory and self.inventory[item] > 0:
            self.inventory[item] -= 1
            print(f"Dispensing {item}... Inventory now: {self.inventory[item]}")
        else:
            print(f"Error: {item} is out of stock.")

    def view_financial_reports(self):
        print("\n--- CONFIDENTIAL FINANCIAL REPORT ---")
        print(f"Total Sales Revenue: ${self.sales_total}")
        print(f"Detailed Inventory Breakdown: {self.inventory}")
        print("--------------------------------------")

class KioskProxy(KioskInterface):
    def __init__(self, role):
        self.role = role
        self.real_kiosk = RealKiosk() # Composition

    def dispense_item(self, item):
        # Public functionality: No role check needed
        print(f"Proxy: Forwarding dispense request for '{item}'...")
        self.real_kiosk.dispense_item(item)

    def view_financial_reports(self):
        # Sensitive functionality: Role check REQUIRED
        print(f"Proxy: Verifying credentials for role '{self.role}'...")
        if self.role.lower() == "admin":
            self.real_kiosk.view_financial_reports()
        else:
            print("ACCESS DENIED: Role 'User' does not have permission to view Financial Reports.")

def main():
    current_role = "User"
    # The user interacts with the Proxy, not the RealKiosk directly
    proxy = KioskProxy(current_role)
    
    while True:
        print(f"\n--- Proxy Design Pattern: Kiosk Operational Access ---")
        print(f"Current System Role: {current_role}")
        print("1. Order Item (Public Access)")
        print("2. View Financial Reports (Protected Access)")
        print("3. Switch Role (Admin/User)")
        print("4. Exit")
        
        choice = input("Enter choice: ")
        
        match choice:
            case "1":
                item = input("Enter item name (Pizza/Burger/Coke): ")
                proxy.dispense_item(item)
            
            case "2":
                proxy.view_financial_reports()
            
            case "3":
                new_role = input("Enter new role (Admin/User): ")
                if new_role.lower() in ["admin", "user"]:
                    current_role = new_role.capitalize()
                    proxy.role = current_role # Update proxy role
                    print(f"System: Role Updated to {current_role}")
                else:
                    print("Invalid Role.")
            
            case "4":
                print("Exiting...")
                break
            
            case _:
                print("Invalid choice.")

if __name__ == "__main__":
    main()
