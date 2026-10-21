"""Fictional demo inventory. Insert missing SKUs only; never overwrite admin edits."""

from datetime import UTC

from backend.app.database import connect, search_text
from backend.app.models import ProductCreate

PRODUCTS = [
    {
        "sku": "LAP-ORBIT-14",
        "name": "Orbit 14",
        "brand": "Northstar",
        "category": "laptop",
        "description": "Portable 14-inch laptop for study and office work. 16 GB memory and 512 GB SSD.",
        "price_cents": 79900,
        "stock_quantity": 8,
        "specifications": {
            "CPU": "Intel Core i5-1335U",
            "RAM": "16 GB",
            "Storage": "512 GB SSD",
            "Display": "14 inch 1920x1200",
            "OS": "Windows 11",
        },
    },
    {
        "sku": "LAP-ORBIT-PRO",
        "name": "Orbit Pro 16",
        "brand": "Northstar",
        "category": "laptop",
        "description": "16-inch creator laptop with dedicated graphics, 32 GB memory, and 1 TB SSD.",
        "price_cents": 159900,
        "stock_quantity": 3,
        "specifications": {
            "CPU": "Intel Core i7-13620H",
            "RAM": "32 GB",
            "Storage": "1 TB SSD",
            "GPU": "NVIDIA RTX 4060",
            "Display": "16 inch 2560x1600",
        },
    },
    {
        "sku": "LAP-EMBER-15",
        "name": "Ember 15",
        "brand": "Redline",
        "category": "laptop",
        "description": "15-inch gaming laptop with 144 Hz display and RTX 4050 graphics.",
        "price_cents": 114900,
        "stock_quantity": 5,
        "specifications": {
            "CPU": "AMD Ryzen 7 7735HS",
            "RAM": "16 GB",
            "Storage": "512 GB SSD",
            "GPU": "NVIDIA RTX 4050",
            "Display": "15.6 inch 144 Hz",
        },
    },
    {
        "sku": "LAP-CLOUD-13",
        "name": "Cloud 13",
        "brand": "Northstar",
        "category": "laptop",
        "description": "Lightweight 13-inch travel laptop with long battery life and 8 GB memory.",
        "price_cents": 64900,
        "stock_quantity": 0,
        "specifications": {
            "CPU": "Intel Core i3-1315U",
            "RAM": "8 GB",
            "Storage": "256 GB SSD",
            "Display": "13.3 inch 1920x1080",
        },
    },
    {
        "sku": "CPU-RYZEN-7600",
        "name": "Ryzen 5 7600",
        "brand": "AMD",
        "category": "component",
        "description": "Desktop processor with six cores for AM5 motherboards. Cooler included.",
        "price_cents": 22900,
        "stock_quantity": 12,
        "specifications": {
            "Socket": "AM5",
            "Cores": "6",
            "Threads": "12",
            "Included cooler": "Yes",
        },
    },
    {
        "sku": "MB-ATLAS-B650",
        "name": "Atlas B650 WiFi",
        "brand": "Redline",
        "category": "component",
        "description": "ATX motherboard for AMD AM5 processors with DDR5 memory slots and Wi-Fi.",
        "price_cents": 18900,
        "stock_quantity": 7,
        "specifications": {
            "Socket": "AM5",
            "Memory": "DDR5",
            "Form factor": "ATX",
            "Wi-Fi": "Yes",
        },
    },
    {
        "sku": "RAM-DDR5-32",
        "name": "Nova DDR5 32 GB Kit",
        "brand": "Northstar",
        "category": "component",
        "description": "Two 16 GB desktop DDR5 memory modules rated at 6000 MT/s.",
        "price_cents": 11900,
        "stock_quantity": 18,
        "specifications": {
            "Capacity": "32 GB (2 x 16 GB)",
            "Type": "DDR5 desktop DIMM",
            "Speed": "6000 MT/s",
        },
    },
    {
        "sku": "SSD-NVME-1TB",
        "name": "Swift NVMe 1 TB",
        "brand": "Northstar",
        "category": "component",
        "description": "M.2 2280 NVMe SSD with PCIe 4.0 interface and 1 TB storage.",
        "price_cents": 8900,
        "stock_quantity": 20,
        "specifications": {
            "Capacity": "1 TB",
            "Interface": "PCIe 4.0 NVMe",
            "Form factor": "M.2 2280",
        },
    },
    {
        "sku": "GPU-RTX-4060",
        "name": "Vector RTX 4060",
        "brand": "Redline",
        "category": "component",
        "description": "Desktop graphics card with 8 GB GDDR6 memory. Check case clearance and power supply before purchase.",
        "price_cents": 32900,
        "stock_quantity": 4,
        "specifications": {
            "GPU": "NVIDIA RTX 4060",
            "VRAM": "8 GB GDDR6",
            "Length": "245 mm",
            "Recommended PSU": "550 W",
        },
    },
    {
        "sku": "PSU-GOLD-650",
        "name": "Core 650 Gold",
        "brand": "Northstar",
        "category": "component",
        "description": "650 W modular ATX power supply rated 80 Plus Gold.",
        "price_cents": 9900,
        "stock_quantity": 10,
        "specifications": {
            "Power": "650 W",
            "Efficiency": "80 Plus Gold",
            "Form factor": "ATX",
            "Modular": "Yes",
        },
    },
    {
        "sku": "MON-VISTA-27",
        "name": "Vista 27 QHD",
        "brand": "Northstar",
        "category": "electronic",
        "description": "27-inch QHD IPS monitor with 144 Hz refresh rate and HDMI and DisplayPort inputs.",
        "price_cents": 27900,
        "stock_quantity": 6,
        "specifications": {
            "Size": "27 inch",
            "Resolution": "2560x1440",
            "Panel": "IPS",
            "Refresh rate": "144 Hz",
            "Inputs": "HDMI, DisplayPort",
        },
    },
    {
        "sku": "KEY-TYPE-87",
        "name": "Type 87 Mechanical",
        "brand": "Redline",
        "category": "electronic",
        "description": "Tenkeyless wired mechanical keyboard with USB-C connection.",
        "price_cents": 7900,
        "stock_quantity": 14,
        "specifications": {
            "Layout": "Tenkeyless",
            "Connection": "USB-C wired",
            "Switch": "Tactile",
        },
    },
    {
        "sku": "MSE-GLIDE-W",
        "name": "Glide Wireless Mouse",
        "brand": "Northstar",
        "category": "electronic",
        "description": "Rechargeable wireless mouse with USB receiver and Bluetooth connectivity.",
        "price_cents": 4900,
        "stock_quantity": 22,
        "specifications": {
            "Connection": "Bluetooth, 2.4 GHz USB receiver",
            "Battery": "Rechargeable",
        },
    },
    {
        "sku": "HDP-SONIC-USB",
        "name": "Sonic USB Headset",
        "brand": "Redline",
        "category": "electronic",
        "description": "USB headset with detachable microphone for calls and gaming.",
        "price_cents": 6900,
        "stock_quantity": 9,
        "specifications": {"Connection": "USB-A", "Microphone": "Detachable"},
    },
    {
        "sku": "LAP-FUTURE-17",
        "name": "Future 17 Preview",
        "brand": "Northstar",
        "category": "laptop",
        "description": "Upcoming 17-inch workstation demo listing. Details are being finalized.",
        "price_cents": 199900,
        "stock_quantity": 0,
        "status": "draft",
        "specifications": {"Display": "17 inch"},
    },
]


def seed(db) -> int:
    from datetime import datetime

    added = 0
    for raw in PRODUCTS:
        data = ProductCreate.model_validate({"status": "published", **raw}).model_dump(mode="json")
        now = datetime.now(UTC)
        data.update(created_at=now, updated_at=now, search_text=search_text(data))
        result = db.products.update_one({"sku": data["sku"]}, {"$setOnInsert": data}, upsert=True)
        added += bool(result.upserted_id)
    return added


def main() -> None:
    client, db = connect()
    try:
        print(f"Inserted {seed(db)} demo products. Existing products were left unchanged.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
