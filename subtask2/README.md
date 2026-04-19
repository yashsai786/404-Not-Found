# 🧠 Smart Kiosk System using Design Patterns

### 🚀 Team: **404 Not Found!** | Group ID: **16**

---

## 👥 Team Members

* **Megha Lalwani - 202512054** *(Group Leader)*
* **Yash Gangwani - 202512048**
* **Harshil Dodwani - 202512044**
* **Bhavika Sainani - 202512053**

---

## 📌 Project Overview

This project presents a **Smart Kiosk System** designed using core **Object-Oriented Design Patterns** to simulate real-world system behavior with modular and scalable architecture.

The system is built to demonstrate how structured design can transform simple logic into a **maintainable, flexible, and extensible system**.

---

## 🧩 Design Patterns Implemented

### 🏭 Factory Pattern

* Dynamic creation of different kiosk types
* Supports extensibility for new kiosk categories
* Separates object creation from business logic

---

### 🛡️ Proxy Pattern

* Implements **role-based access control**
* Restricts sensitive operations (like financial reports)
* Acts as a secure intermediary between user and system

---

### 🎯 Strategy Pattern

* Enables **runtime behavior selection**
* Used for:

  * 💳 User-selected payment methods
  * 🤖 Arm-based dispensing logic
* Improves flexibility and modularity

---

## 🔗 Design Pattern Mapping in System  

This project not only implements design patterns individually, but also clearly maps them to real-world system functionalities:

- 🏭 **Factory Pattern → Kiosk Type Management**  
  Used to create different types of kiosks such as **Food** and **Pharmacy** dynamically.  
  This allows easy extension of new kiosk categories without modifying existing logic.

- 🛡️ **Proxy Pattern → Role-Based Access Control (Admin/User)**  
  The separation between **Admin Mode** and **User Mode** is implemented using the Proxy Pattern.  
  It ensures that sensitive operations like:
  - Viewing financial data  
  - Modifying inventory  
  are accessible **only to authorized roles (Admin)**.

- 🎯 **Strategy Pattern → Payment & Dispensing Behavior**  
  Used to dynamically select:
  - User-preferred payment methods (UPI, Card, Cash)  
  - Dispensing logic (arm-based selection)  
  at runtime without changing the core system.

---


## 🖥️ System Modes & User Experience

The system is designed with a **dual-mode architecture** to simulate real-world kiosk behavior.

---

### 🔐 Admin Mode (Privileged Access)

To access admin controls, the password is:
👉 **`admin`**

Admin Mode provides full system control:

* ➕ Add new items to the kiosk
* 🗑️ Delete existing items
* ✏️ Update item details (price & stock)
* 📊 View real-time system logs

This mode acts as the **central control layer** of the system.

---

### 👤 User Mode (Public Interaction)

User Mode is designed for simplicity and ease of use:

* 📦 View available products
* 💰 Check item pricing
* ⚡ Request item dispensing

All critical operations are hidden, ensuring a **safe and smooth user experience**.

---

## 🎨 Interface Preview

### 🔐 Admin Interface

* Inventory management dashboard
* Data injection and modification tools
* Real-time system logs

---

### 👤 User Interface

* Clean product display
* Simple interaction flow
* Fast dispensing system

---

## 📁 Folder Structure

```bash
allthree/
  ├── templates/
  ├── __init__.py
  ├── kiosk_logic.py
  └── kiosk_master.db

Basic Cli/
  ├── cli_factory.py
  ├── cli_proxy.py
  └── cli_strategy.py

factory_model/
  ├── app.py
  ├── kiosk_logic.py
  ├── index.html
  └── kiosk_os.db

proxy_model/
  ├── app.py
  ├── kiosk_logic.py
  ├── index.html
  └── proxy_os.db

strategy_model/
  ├── app.py
  ├── kiosk_logic.py
  ├── index.html
  └── strategy_os.db

.gitignore
kiosk_master.db
main.py
README.md
```

---

## 🏗️ System Architecture & Execution Modes  

This project is designed with multiple execution layers to demonstrate flexibility in interaction and system design:

- 🌐 **Integrated Full Project (`allthree/` + `main.py`)** *(Primary)*  
  - All three design patterns unified into a single cohesive system  
  - Entry point: `main.py` at the project root  
  - Shared logic in `allthree/kiosk_logic.py` and persistent storage via `kiosk_master.db`  
  - Web templates served from `allthree/templates/`  
  - This is the **recommended way to run the full system**

- 🖥️ **CLI Modules (`Basic Cli/`)**  
  - Terminal-based implementations  
  - Focused purely on logic and design pattern demonstration  
  - No frontend or database dependency  

- 🌐 **Standalone Backend + Frontend Modules (`factory_model`, `proxy_model`, `strategy_model`)**  
  - Individual pattern implementations with separate web interfaces  
  - Each includes `index.html`, `app.py`, and its own `.db` file  
  - Useful for isolated pattern testing and demonstration  

---

## ⚙️ How to Run

### 🚀 Integrated System (All Three Patterns — Recommended)

Run the full integrated project from the root directory:

```bash
python main.py
```

This launches the complete Smart Kiosk System with all three design patterns (Factory, Proxy, Strategy) working together.

---

### 🖥️ CLI Versions

Run individual design pattern implementations:

```bash
python cli_factory.py
python cli_proxy.py
python cli_strategy.py
```

---

### 🌐 Standalone Backend Versions

Each module runs independently:

```bash
cd factory_model
python app.py
```

```bash
cd proxy_model
python app.py
```

```bash
cd strategy_model
python app.py
```

---

## 🎯 Key Features

* ✅ All three design patterns integrated into a unified system (`allthree/`)
* ✅ Single entry point via `main.py` for the full project
* ✅ Independent implementations also available for each pattern
* ✅ Modular and scalable architecture
* ✅ CLI + Web-based interaction
* ✅ Role-based access control
* ✅ Real-world kiosk simulation

---

## 🧠 Learning Outcomes

* Strong understanding of **OOP principles**
* Practical implementation of **Design Patterns**
* Experience with **modular system design**
* Improved problem-solving using structured approaches

---

## 💡 Design Philosophy

This project emphasizes:

* 🔒 Security through access control (Proxy)
* 🧩 Separation of concerns (Factory & Strategy)
* ⚙️ Flexibility and scalability
* 🧠 Clean and maintainable code structure

---

## 🏁 Final Note

This project is not just an implementation — it is a demonstration of how **design patterns can be applied to build structured, real-world systems**.

From controlled administrative power to seamless user interaction,
every component reflects thoughtful design and engineering.

✨ *Built with clarity, collaboration, and clean architecture.*

---

⭐ *If you found this project interesting, consider giving it a star!*