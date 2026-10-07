"""Grounded catalogue tools exposed to the PydanticAI shop assistant."""

from __future__ import annotations

import re
from typing import TypeVar

from pydantic_ai import Agent, RunContext

from audit import append_event
from db import read_product, read_products
from models import DescriptionLookup, PriceLookup, ProductCard, ShopDeps, StockLookup


MAX_MATCHES = 8
STOP_WORDS = {"a", "an", "any", "are", "can", "do", "for", "have", "i", "in", "is", "me", "of", "show", "some", "the", "there", "what", "which", "with", "you"}
ALIASES = {"hoodies": "hoodie", "tees": "t-shirt", "tee": "t-shirt", "tshirts": "t-shirt", "tshirt": "t-shirt", "shirts": "shirt", "sweatshirts": "sweatshirt", "jackets": "jacket", "fleeces": "fleece", "crewnecks": "crewneck"}


def _tokens(text: str) -> list[str]:
    raw = re.findall(r"[a-z0-9-]+", text.casefold())
    return [ALIASES.get(token, token) for token in raw if token not in STOP_WORDS]


def _score(product: dict, tokens: list[str]) -> int:
    name = product["name"].casefold()
    kind = product["garment_type"].casefold()
    tags = " ".join(product["search_tags"]).casefold()
    description = product["description"].casefold()
    score = 0
    for token in tokens:
        if token in name:
            score += 5
        if token in kind:
            score += 4
        if token in tags:
            score += 3
        if token in description:
            score += 1
    return score


def search_catalogue(query: str, limit: int = MAX_MATCHES) -> list[ProductCard]:
    """Rank real catalogue items by the shopper's words, with a strict result cap."""
    tokens = _tokens(query)
    if not tokens:
        return []
    ranked = [(product, _score(product, tokens)) for product in read_products()]
    ranked = [item for item in ranked if item[1] > 0]
    ranked.sort(key=lambda item: (-item[1], item[0]["name"].casefold()))
    return [ProductCard.model_validate(product) for product, _ in ranked[: max(1, min(limit, MAX_MATCHES))]]


def resolve_product(query: str, page_product_id: str | None = None) -> dict | None:
    """Resolve an explicit item, declining vague matches instead of guessing."""
    query = query.strip()
    if page_product_id and (not query or query.casefold() in {"this", "this item", "this product", "it", "the item"}):
        return read_product(page_product_id)
    if not query:
        return None
    products = read_products()
    for product in products:
        if query.casefold() in {product["product_id"].casefold(), product["name"].casefold()}:
            return product
    partial_name_matches = [item for item in products if query.casefold() in item["name"].casefold()]
    if len(partial_name_matches) == 1:
        return partial_name_matches[0]
    if len(partial_name_matches) > 1:
        return None
    tokens = _tokens(query)
    ranked = sorted(((item, _score(item, tokens)) for item in products), key=lambda pair: -pair[1])
    if not ranked or ranked[0][1] == 0 or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
        return None
    return ranked[0][0]


def _attach_product(ctx: RunContext[ShopDeps], product: dict | None) -> None:
    if product and not any(item.product_id == product["product_id"] for item in ctx.deps.matched_products):
        ctx.deps.matched_products.append(ProductCard.model_validate(product))


AgentT = TypeVar("AgentT", bound=Agent)


def register_tools(agent: AgentT) -> AgentT:
    @agent.tool
    def search_products(ctx: RunContext[ShopDeps], query: str) -> list[ProductCard]:
        """Find up to eight real products matching a garment type, color, theme, or search phrase."""
        matches = search_catalogue(query)
        ctx.deps.matched_products = matches
        append_event("search_products", args={"query": query[:80]}, result={"count": len(matches), "ids": [item.product_id for item in matches]})
        return matches

    @agent.tool
    def get_product_description(ctx: RunContext[ShopDeps], product_query: str = "this") -> DescriptionLookup | None:
        """Look up a product's actual description, garment type, and colors in the database."""
        product = resolve_product(product_query, ctx.deps.page_product_id)
        _attach_product(ctx, product)
        append_event("get_product_description", args={"query": product_query[:80]}, result={"product_id": product["product_id"] if product else None})
        if not product:
            return None
        return DescriptionLookup.model_validate(product)

    @agent.tool
    def get_product_price(ctx: RunContext[ShopDeps], product_query: str = "this") -> PriceLookup | None:
        """Read the current catalogue price for a specific product; never guess a price."""
        product = resolve_product(product_query, ctx.deps.page_product_id)
        _attach_product(ctx, product)
        append_event("get_product_price", args={"query": product_query[:80]}, result={"product_id": product["product_id"] if product else None, "price": product["price"] if product else None})
        if not product:
            return None
        return PriceLookup.model_validate(product)

    @agent.tool
    def get_product_stock(ctx: RunContext[ShopDeps], product_query: str = "this", size: str | None = None) -> StockLookup | None:
        """Read live inventory by size for a product, including zero-stock sizes."""
        product = resolve_product(product_query, ctx.deps.page_product_id)
        _attach_product(ctx, product)
        append_event("get_product_stock", args={"query": product_query[:80], "size": size}, result={"product_id": product["product_id"] if product else None})
        if not product:
            return None
        requested = size.strip().upper() if size else None
        stock = product["inventory"]
        if requested:
            stock = [item for item in stock if item["size"].upper() == requested]
        return StockLookup(product_id=product["product_id"], name=product["name"], requested_size=requested, inventory=stock, total_stock=product["total_stock"])

    return agent
