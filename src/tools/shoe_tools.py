from typing import Dict, Any, Union

# 1. Mock Dataset: 7 Đôi giày từ Adidas, Nike, Puma
SHOE_DATABASE = {
    "NK-8821": {"brand": "Nike", "name": "Air Force 1", "price": 120.0, "stock": 15},
    "NK-9922": {"brand": "Nike", "name": "Air Max 97", "price": 160.0, "stock": 0},
    "AD-1102": {"brand": "Adidas", "name": "Ultraboost 22", "price": 190.0, "stock": 8},
    "AD-3344": {"brand": "Adidas", "name": "Stan Smith", "price": 95.0, "stock": 25},
    "PM-5511": {"brand": "Puma", "name": "Suede Classic", "price": 70.0, "stock": 50},
    "PM-7722": {"brand": "Puma", "name": "RS-X Toys", "price": 110.0, "stock": 3},
    "NK-4455": {"brand": "Nike", "name": "Pegasus 40", "price": 130.0, "stock": 10}
}

# Bước 1.5: Xử lý ngoại lệ "Out of dataset"
# Nếu không tìm thấy trong DB, ta trả về text đặc thù để OpenAPI tự suy luận bằng kiến thức có sẵn
OUT_OF_DATASET_MSG = "NOT_IN_DATABASE. This product is not in our internal inventory database. You may answer using your general external knowledge about this shoe."

def search_shoes_by_brand(brand: str) -> str:
    """
    Searches for all available shoe models in the internal database by brand name.
    Input: brand (str) - The brand name (e.g., 'Nike', 'Adidas', 'Puma').
    Returns: (str) A list of shoe SKUs and names, or a message if the brand has no models in our system.
    """
    brand = brand.capitalize()
    results = [f"[{sku}] {info['name']}" for sku, info in SHOE_DATABASE.items() if info["brand"] == brand]
    if not results:
        return f"No shoes from {brand} found in internal database."
    return ", ".join(results)

def check_shoe_availability(sku: str) -> str:
    """
    Checks the inventory stock level for a specific shoe.
    Input: sku (str) - The unique product ID (e.g., 'NK-8821').
    Returns: (str) The available quantity, or out of dataset message if not found.
    """
    oku_upper = sku.upper()
    if oku_upper not in SHOE_DATABASE:
        return OUT_OF_DATASET_MSG
    stock = SHOE_DATABASE[oku_upper]["stock"]
    return f"{stock} units available." if stock > 0 else "0 units available (Out of stock)."

def check_price(sku: str) -> str:
    """
    Retrieves the exact price of a shoe.
    Input: sku (str) - The unique product ID (e.g., 'AD-1102').
    Returns: (str) The price in USD format, or out of dataset message if not found.
    """
    oku_upper = sku.upper()
    if oku_upper not in SHOE_DATABASE:
        return OUT_OF_DATASET_MSG
    price = SHOE_DATABASE[oku_upper]["price"]
    return f"${price:.2f}"
