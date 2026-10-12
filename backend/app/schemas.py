from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Reason = Literal["RESTOCK", "SALE", "RETURN", "DAMAGED", "CORRECTION"]


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(default="General", min_length=1, max_length=60)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    reorder_level: int = Field(default=10, ge=0)


class ProductCreate(ProductBase):
    sku: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9-]+$")
    quantity: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    category: str | None = Field(default=None, min_length=1, max_length=60)
    unit_price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    reorder_level: int | None = Field(default=None, ge=0)


class ProductOut(ProductCreate):
    id: int
    low_stock: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MovementCreate(BaseModel):
    change: int = Field(description="Positive adds stock, negative removes it")
    reason: Reason
    note: str = Field(default="", max_length=200)

    @field_validator("change")
    @classmethod
    def not_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("change must not be zero")
        return value


class MovementOut(MovementCreate):
    id: int
    product_id: int
    product_name: str
    created_at: datetime


class CategoryCount(BaseModel):
    category: str
    products: int
    units: int


class StatsOut(BaseModel):
    products: int
    units: int
    inventory_value: Decimal
    low_stock: int
    out_of_stock: int
    categories: list[CategoryCount]
