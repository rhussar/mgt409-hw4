"""Final factual guard for exact product price and size questions."""

from __future__ import annotations

import re

from db import read_products


SIZE_ALIASES = {
    "extra extra large": "XXL", "2xl": "XXL", "xxl": "XXL",
    "extra large": "XL", "xl": "XL", "large": "L", "medium": "M", "small": "S", "extra small": "XS",
    "xs": "XS", "l": "L", "m": "M", "s": "S",
}


def exact_product_from_message(message: str, page_product: dict | None) -> dict | None:
    lower = message.casefold()
    named = [item for item in read_products() if item["name"].casefold() in lower]
    if named:
        return max(named, key=lambda item: len(item["name"]))
    if page_product and (
        re.search(r"\b(this|it|these)\b", lower)
        or not re.search(r"\b(hoodie|shirt|jacket|crewneck|fleece|sweater|tee)\b", lower)
    ):
        return page_product
    return None


def grounded_fact_reply(message: str, product: dict | None) -> str | None:
    """Return a DB-built answer only when the item and factual intent are clear."""
    if product is None:
        return None
    lower = message.casefold()
    asks_price = bool(re.search(r"\b(price|cost|how much|dollars?)\b", lower))
    asks_stock = bool(re.search(r"\b(stock|availability|available|sizes?)\b", lower))
    requested_size = None
    for phrase in sorted(SIZE_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(phrase)}\b", lower):
            requested_size = SIZE_ALIASES[phrase]
            break
    asks_stock = asks_stock or requested_size is not None
    if not asks_price and not asks_stock:
        return None

    sentences = []
    if asks_price:
        sentences.append(f"{product['name']} costs ${product['price']:.2f}.")
    if asks_stock and requested_size:
        match = next((item for item in product["inventory"] if item["size"] == requested_size), None)
        if match is None:
            sentences.append(f"I cannot verify size {requested_size} for this item.")
        elif match["quantity"] == 0:
            sentences.append(f"Size {requested_size} is out of stock.")
        else:
            sentences.append(f"Size {requested_size} has {match['quantity']} in stock.")
    elif asks_stock:
        available = [f"{item['size']} ({item['quantity']})" for item in product["inventory"] if item["quantity"] > 0]
        sentences.append("Available sizes: " + ", ".join(available) + "." if available else "This item is out of stock in every listed size.")
    return " ".join(sentences)
