"""Validated request, response, and catalogue shapes shared by the API and agent."""

from __future__ import annotations

from typing import Literal
from dataclasses import dataclass, field

from pydantic import BaseModel, EmailStr, Field, field_validator


class InventoryItem(BaseModel):
    size: str
    quantity: int = Field(ge=0)


class ProductCard(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    image_url: str
    price: float = Field(ge=0)
    total_stock: int = Field(ge=0)


class Product(ProductCard):
    colors: list[str]
    search_tags: list[str]
    inventory: list[InventoryItem]


class UserPublic(BaseModel):
    id: int
    name: str
    first_name: str | None
    last_name: str | None
    email: EmailStr
    created_at: str


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("first_name", "last_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be blank")
        return cleaned


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user: UserPublic


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    page_product_id: str | None = Field(default=None, max_length=150)

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message cannot be blank")
        return cleaned


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str


class DescriptionLookup(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]


class PriceLookup(BaseModel):
    product_id: str
    name: str
    price: float = Field(ge=0)


class StockLookup(BaseModel):
    product_id: str
    name: str
    requested_size: str | None = None
    inventory: list[InventoryItem]
    total_stock: int = Field(ge=0)


@dataclass
class ShopDeps:
    user_id: int | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    page_product_id: str | None = None
    matched_products: list[ProductCard] = field(default_factory=list)
