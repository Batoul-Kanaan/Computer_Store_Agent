from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    field_validator,
)

SKU = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Z0-9][A-Z0-9-]{2,39}$"),
]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]


class Category(str, Enum):
    laptop = "laptop"
    component = "component"
    electronic = "electronic"


class ProductStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class ProductFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ShortText
    brand: ShortText
    category: Category
    description: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=10, max_length=2000)
    ]
    price_cents: int = Field(ge=0, le=100_000_000)
    stock_quantity: int = Field(ge=0, le=1_000_000)
    image_url: HttpUrl | None = None
    specifications: dict[str, str] = Field(default_factory=dict)
    status: ProductStatus = ProductStatus.draft

    @field_validator("specifications")
    @classmethod
    def validate_specs(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 30 or any(
            not k.strip() or len(k) > 60 or len(v) > 200 for k, v in value.items()
        ):
            raise ValueError(
                "Use up to 30 specifications, with keys <= 60 and values <= 200 characters"
            )
        return {k.strip(): v.strip() for k, v in value.items()}


class ProductCreate(ProductFields):
    sku: SKU


class ProductUpdate(ProductFields):
    """The admin editor submits a full replacement so omitted fields cannot silently reset."""


class ProductOut(ProductCreate):
    created_at: datetime
    updated_at: datetime


class AdminLogin(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class AccountSignup(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=256)


class AdminIdentity(BaseModel):
    username: str
    csrf_token: str
    role: str = "admin"


class ChatTurn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=8)


class ChatResponse(BaseModel):
    answer: str
    products: list[ProductOut] = Field(default_factory=list)
