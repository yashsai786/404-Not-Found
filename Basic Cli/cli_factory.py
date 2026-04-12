import sys

class Kiosk:
    def __init__(self, name, kiosk_type):
        self.name = name
        self.kiosk_type = kiosk_type
        self.inventory = [] # List of items in this kiosk

    def add_item(self, item_name):
        self.inventory.append(item_name)
        print(f"Admin: Added '{item_name}' to {self.name} ({self.kiosk_type})")

    def dispense_item(self, item_name):
        if item_name in self.inventory:
            self.inventory.remove(item_name)
            return True
        return False

class FoodKiosk(Kiosk):
    def __init__(self, name):
        super().__init__(name, "Food")

class PharmacyKiosk(Kiosk):
    def __init__(self, name):
        super().__init__(name, "Pharmacy")

class CustomKiosk(Kiosk):
    def __init__(self, name, kiosk_type):
        super().__init__(name, kiosk_type)

class KioskFactory:
    def __init__(self):
        self.available_types = ["Food", "Pharmacy"]

    def create_kiosk(self, kiosk_type, name):
        match kiosk_type.lower():
            case "food":
                return FoodKiosk(name)
            case "pharmacy":
                return PharmacyKiosk(name)
            case _:
                if kiosk_type.capitalize() in self.available_types:
                    return CustomKiosk(name, kiosk_type.capitalize())
                return None

    def register_new_type(self, type_name):
        if type_name.capitalize() not in self.available_types:
            self.available_types.append(type_name.capitalize())
            return True
        return False

def main():
    factory = KioskFactory()
    
    # Pre-populating with initial kiosks and products as requested
    k1 = FoodKiosk("Central Food Kiosk")
    k1.inventory = ["Pizza", "Burger", "Coke"]
    
    k2 = PharmacyKiosk("Quick Meds Kiosk")
    k2.inventory = ["Paracetamol", "Aspirin", "Bandages"]
    
    active_kiosks = [k1, k2] 

    while True:
        print("\n--- Factory Kiosk System (CLI) ---")
        print("1. Admin Mode (Register Type / Manage Inventory)")
        print("2. User Mode (Use/Dispense from Kiosk)")
        print("3. Exit")
        
        main_choice = input("Select Mode: ")

        match main_choice:
            case "1":
                print("\n[Admin Mode]")
                print("1. Register New Kiosk Type")
                print("2. Create New Kiosk Instance")
                print("3. Add Items to Kiosk Inventory")
                admin_choice = input("Select Admin Action: ")

                match admin_choice:
                    case "1":
                        new_type = input("Enter new kiosk type name: ")
                        if factory.register_new_type(new_type):
                            print(f"Success: Type '{new_type}' registered.")
                        else:
                            print("Error: Type already exists.")

                    case "2":
                        print(f"Available Types: {', '.join(factory.available_types)}")
                        k_type = input("Enter Type: ")
                        k_name = input("Enter Name for Kiosk: ")
                        new_kiosk = factory.create_kiosk(k_type, k_name)
                        if new_kiosk:
                            active_kiosks.append(new_kiosk)
                            print(f"Kiosk '{k_name}' created successfully.")
                        else:
                            print("Error: Invalid Type.")

                    case "3":
                        if not active_kiosks:
                            print("No kiosks created yet.")
                        else:
                            for idx, k in enumerate(active_kiosks):
                                print(f"{idx + 1}. {k.name} ({k.kiosk_type})")
                            k_idx = int(input("Select Kiosk # to add item to: ")) - 1
                            item = input("Enter item name to add: ")
                            active_kiosks[k_idx].add_item(item)

            case "2":
                print("\n[User Mode]")
                if not active_kiosks:
                    print("No kiosks available in the system.")
                    continue
                
                for idx, k in enumerate(active_kiosks):
                    print(f"{idx + 1}. {k.name} ({k.kiosk_type})")
                
                try:
                    k_idx = int(input("Select Kiosk # to use: ")) - 1
                    selected_kiosk = active_kiosks[k_idx]
                    
                    print(f"\nWelcome to {selected_kiosk.name}!")
                    print(f"Inventory: {', '.join(selected_kiosk.inventory) if selected_kiosk.inventory else 'Empty'}")
                    
                    if selected_kiosk.inventory:
                        item_to_buy = input("Enter item name to dispense: ")
                        if selected_kiosk.dispense_item(item_to_buy):
                            print(f"SUCCESS: Dispensing {item_to_buy}... Enjoy!")
                        else:
                            print("Error: Item not in stock.")
                    else:
                        print("Visit back later when Admin adds items.")
                except (ValueError, IndexError):
                    print("Invalid selection.")

            case "3":
                print("Exiting...")
                sys.exit()
            
            case _:
                print("Invalid choice.")

if __name__ == "__main__":
    main()
