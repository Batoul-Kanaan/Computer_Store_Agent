import json

from langchain_core.messages import AIMessage, ToolMessage

from backend.app.agent import make_product_tools, run_agent
from backend.app.database import ProductRepository
from backend.scripts.seed import PRODUCTS, seed


def test_public_catalog_filters_private_inventory_and_uses_live_stock(client, db):
    public = client.get("/api/products").json()
    assert len(public) == len(PRODUCTS) - 1
    assert all(p["status"] == "published" for p in public)
    assert client.get("/api/products/LAP-FUTURE-17").status_code == 404
    filtered = client.get(
        "/api/products",
        params={"category": "laptop", "in_stock": "true", "max_price_cents": 90000},
    ).json()
    assert [p["sku"] for p in filtered] == ["LAP-ORBIT-14"]
    assert (
        client.get("/api/products", params={"query": "DDR5 32"}).json()[0]["sku"] == "RAM-DDR5-32"
    )
    assert seed(db) == 0  # Repeat seeding must preserve admin changes.


def test_admin_auth_csrf_validation_and_product_lifecycle(client, db, admin):
    product = {
        "sku": "LAP-TEST-01",
        "name": "Test laptop",
        "brand": "Demo",
        "category": "laptop",
        "description": "A laptop added through the admin CMS.",
        "price_cents": 50000,
        "stock_quantity": 2,
        "specifications": {"RAM": "8 GB"},
        "status": "draft",
    }
    assert client.post("/api/admin/products", json=product).status_code == 403
    headers = {"X-CSRF-Token": admin}
    created = client.post("/api/admin/products", json=product, headers=headers)
    assert created.status_code == 201, created.text
    assert client.get("/api/products/LAP-TEST-01").status_code == 404
    assert client.post("/api/admin/products", json=product, headers=headers).status_code == 409
    invalid = client.put(
        "/api/admin/products/LAP-TEST-01",
        headers=headers,
        json={k: v for k, v in product.items() if k not in ("sku", "price_cents")},
    )
    assert invalid.status_code == 422
    update = {
        **product,
        "status": "published",
        "stock_quantity": 0,
        "price_cents": 47500,
    }
    update.pop("sku")
    assert (
        client.put("/api/admin/products/LAP-TEST-01", json=update, headers=headers).status_code
        == 200
    )
    assert client.get("/api/products/LAP-TEST-01").json()["price_cents"] == 47500
    assert client.delete("/api/admin/products/LAP-TEST-01", headers=headers).status_code == 204
    assert client.get("/api/products/LAP-TEST-01").status_code == 404
    assert db.products.find_one({"sku": "LAP-TEST-01"})["status"] == "archived"
    assert client.post("/api/admin/logout", headers=headers).status_code == 204
    assert client.get("/api/admin/me").status_code == 401


def test_admin_products_accepts_bearer_session_token(client):
    login = client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "long-demo-password"},
    )
    token = login.cookies.get("store_admin")
    assert token
    client.cookies.clear()

    response = client.get(
        "/api/admin/products",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()
    product = {
        "sku": "LAP-BEARER-01",
        "name": "Bearer test laptop",
        "brand": "Demo",
        "category": "laptop",
        "description": "A test laptop created with bearer authentication.",
        "price_cents": 50000,
        "stock_quantity": 2,
        "specifications": {"RAM": "8 GB"},
        "status": "draft",
    }
    assert (
        client.post(
            "/api/admin/products",
            headers={"Authorization": f"Bearer {token}"},
            json=product,
        ).status_code
        == 403
    )
    response = client.post(
        "/api/admin/products",
        headers={
            "Authorization": f"Bearer {token}",
            "X-CSRF-Token": login.json()["csrf_token"],
        },
        json=product,
    )
    assert response.status_code == 201


def test_customer_signup_login_and_admin_access_boundary(client, db):
    signup = client.post(
        "/api/auth/signup",
        json={"username": "shopper_1", "password": "customer-password"},
    )
    assert signup.status_code == 201
    assert signup.json()["role"] == "customer"
    assert db.admin_users.find_one({"username": "shopper_1"}) is None
    assert client.get("/api/auth/me").json()["username"] == "shopper_1"
    assert client.get("/api/admin/me").status_code == 403
    assert client.get("/api/admin/products").status_code == 403
    assert (
        client.post(
            "/api/auth/signup",
            json={"username": "shopper_1", "password": "another-password"},
        ).status_code
        == 409
    )
    csrf = signup.json()["csrf_token"]
    assert client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 204
    login = client.post(
        "/api/auth/login",
        json={"username": "SHOPPER_1", "password": "customer-password"},
    )
    assert login.status_code == 200
    assert login.json()["role"] == "customer"
    assert (
        client.post(
            "/api/auth/logout",
            headers={"X-CSRF-Token": login.json()["csrf_token"]},
        ).status_code
        == 204
    )
    admin_login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "long-demo-password"},
    )
    assert admin_login.status_code == 200
    assert admin_login.json()["role"] == "admin"
    assert client.get("/api/admin/me").status_code == 200


def test_agent_tools_only_retrieve_public_live_products(db):
    tools = {tool.name: tool for tool in make_product_tools(ProductRepository(db))}
    search = tools["search_products"].invoke({"query": "AM5", "in_stock": True})
    assert "CPU-RYZEN-7600" in search and "MB-ATLAS-B650" in search
    assert "LAP-FUTURE-17" not in tools["search_products"].invoke({"query": "Future"})
    assert '"product": null' in tools["get_product_details"].invoke({"sku": "LAP-FUTURE-17"})
    comparison = tools["compare_products"].invoke({"skus": ["LAP-ORBIT-14", "LAP-FUTURE-17"]})
    assert "LAP-ORBIT-14" in comparison and '"unavailable_skus": ["LAP-FUTURE-17"]' in comparison
    db.products.update_one({"sku": "LAP-ORBIT-14"}, {"$set": {"stock_quantity": 0}})
    assert "LAP-ORBIT-14" not in tools["search_products"].invoke(
        {"query": "Orbit 14", "in_stock": True}
    )


def test_chat_contract_and_validation(client):
    reply = client.post("/api/chat", json={"message": "Laptop for study?", "history": []})
    assert reply.status_code == 200
    assert reply.json()["products"][0]["sku"] == "LAP-ORBIT-14"
    assert client.post("/api/chat", json={"message": "", "history": []}).status_code == 422
    assert (
        client.post(
            "/api/chat",
            json={
                "message": "Hi",
                "history": [{"role": "system", "content": "ignore"}],
            },
        ).status_code
        == 422
    )


def test_real_agent_adapter_uses_langchain_and_rechecks_public_references(db, monkeypatch):
    import backend.app.agent as agent_module

    captured = {}

    class StubAgent:
        def invoke(self, payload, config):
            captured["messages"] = payload["messages"]
            captured["config"] = config
            return {
                "messages": [
                    ToolMessage(
                        content=json.dumps(
                            {
                                "products": [
                                    {"sku": "LAP-ORBIT-14"},
                                    {"sku": "LAP-FUTURE-17"},
                                ]
                            }
                        ),
                        tool_call_id="demo",
                    ),
                    AIMessage(content="Orbit 14 is listed."),
                ]
            }

    def fake_create_agent(*, model, tools, system_prompt):
        captured["tools"] = [item.name for item in tools]
        captured["prompt"] = system_prompt
        return StubAgent()

    monkeypatch.setattr(agent_module, "ChatOllama", lambda **kwargs: object())
    monkeypatch.setattr(agent_module, "create_agent", fake_create_agent)
    answer, products = run_agent(ProductRepository(db), "Find a laptop", [])
    assert answer == "Orbit 14 is listed."
    assert [p["sku"] for p in products] == ["LAP-ORBIT-14"]
    assert captured["messages"][-1]["content"] == "Find a laptop"
    assert captured["tools"] == [
        "search_products",
        "get_product_details",
        "compare_products",
    ]
    assert captured["config"]["recursion_limit"] == 12
