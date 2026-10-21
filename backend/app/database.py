import re
from datetime import UTC, datetime

from fastapi import Request
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.database import Database

from backend.app.config import settings
from backend.app.models import ProductCreate, ProductUpdate


def connect() -> tuple[MongoClient, Database]:
    client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=3000, tz_aware=True)
    client.admin.command("ping")
    db = client[settings.mongo_database]
    ensure_indexes(db)
    return client, db


def ensure_indexes(db: Database) -> None:
    db.products.create_index("sku", unique=True)
    db.products.create_index(
        [("status", ASCENDING), ("category", ASCENDING), ("price_cents", ASCENDING)]
    )
    db.products.create_index([("status", ASCENDING), ("price_cents", ASCENDING)])
    db.admin_users.create_index("username", unique=True)
    db.store_users.create_index("username", unique=True)
    db.admin_sessions.create_index("expires_at", expireAfterSeconds=0)


def get_db(request: Request) -> Database:
    return request.app.state.db


def product_output(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k not in ("_id", "search_text")}


def search_text(product: dict) -> str:
    def values(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield str(key)
                yield from values(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from values(item)
        elif value is not None:
            yield str(value)

    fields = [product.get(key) for key in ("sku", "name", "brand", "category", "description")]
    fields.append(product.get("specifications", {}))
    return " ".join(text.lower() for field in fields for text in values(field))


class ProductRepository:
    def __init__(self, db: Database):
        self.collection = db.products

    def list(
        self,
        *,
        public: bool,
        query: str = "",
        category: str | None = None,
        brand: str | None = None,
        max_price_cents: int | None = None,
        min_price_cents: int | None = None,
        in_stock: bool = False,
        limit: int = 60,
        sort_by: str = "sku",
    ) -> list[dict]:
        filters: dict = {"status": "published"} if public else {}
        if category:
            filters["category"] = category
        if brand:
            filters["brand"] = {"$regex": re.escape(brand), "$options": "i"}
        if min_price_cents is not None or max_price_cents is not None:
            filters["price_cents"] = {}
            if min_price_cents is not None:
                filters["price_cents"]["$gt"] = min_price_cents
            if max_price_cents is not None:
                filters["price_cents"]["$lte"] = max_price_cents
        if in_stock:
            filters["stock_quantity"] = {"$gt": 0}

        terms = query.strip().split()[:8]
        if terms:
            filters["$and"] = [
                {"search_text": {"$regex": re.escape(term), "$options": "i"}}
                for term in terms
            ]

        ordering = {
            "sku": [("sku", ASCENDING)],
            "price_asc": [("price_cents", ASCENDING), ("sku", ASCENDING)],
            "price_desc": [("price_cents", DESCENDING), ("sku", ASCENDING)],
        }
        if sort_by not in ordering:
            raise ValueError("Invalid product sort order")
        if not 1 <= limit <= 500:
            raise ValueError("Product search limit must be between 1 and 500")

        cursor = self.collection.find(filters).sort(ordering[sort_by]).limit(limit)
        return [product_output(doc) for doc in cursor]

    def get(self, sku: str, *, public: bool = False) -> dict | None:
        filters = {"sku": sku.upper()}
        if public:
            filters["status"] = "published"
        doc = self.collection.find_one(filters)
        return product_output(doc) if doc else None

    def create(self, product: ProductCreate) -> dict:
        now = datetime.now(UTC)
        data = product.model_dump(mode="json")
        data.update(created_at=now, updated_at=now)
        data["search_text"] = search_text(data)
        self.collection.insert_one(data)
        return self.get(product.sku)

    def update(self, sku: str, product: ProductUpdate) -> dict | None:
        data = product.model_dump(mode="json")
        data["sku"] = sku.upper()
        data["search_text"] = search_text(data)
        data.pop("sku")
        data["updated_at"] = datetime.now(UTC)
        doc = self.collection.find_one_and_update(
            {"sku": sku.upper()}, {"$set": data}, return_document=ReturnDocument.AFTER
        )
        return product_output(doc) if doc else None

    def archive(self, sku: str) -> bool:
        result = self.collection.update_one(
            {"sku": sku.upper()},
            {"$set": {"status": "archived", "updated_at": datetime.now(UTC)}},
        )
        return result.matched_count > 0
