import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pymongo.errors import DuplicateKeyError

from backend.app.agent import run_agent
from backend.app.auth import (
    COOKIE_NAME,
    authenticate,
    authenticate_account,
    hash_password,
    new_session,
    require_admin,
    require_csrf,
    require_session,
    require_session_csrf,
    revoke_session,
)
from backend.app.config import settings
from backend.app.database import ProductRepository, get_db
from backend.app.models import (
    AccountSignup,
    AdminIdentity,
    AdminLogin,
    Category,
    ChatRequest,
    ChatResponse,
    ProductCreate,
    ProductOut,
    ProductUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/api",
        max_age=settings.admin_session_hours * 3600,
    )


def repo_for(db=Depends(get_db)) -> ProductRepository:
    return ProductRepository(db)


@router.get("/health")
def health(db=Depends(get_db)):
    db.command("ping")
    return {"status": "ok"}


@router.get("/products", response_model=list[ProductOut])
def products(
    query: str = Query(default="", max_length=120),
    category: Category | None = None,
    brand: str | None = Query(default=None, max_length=80),
    max_price_cents: int | None = Query(default=None, ge=0),
    in_stock: bool = False,
    repo: ProductRepository = Depends(repo_for),
):
    return repo.list(
        public=True,
        query=query,
        category=category,
        brand=brand,
        max_price_cents=max_price_cents,
        in_stock=in_stock,
    )


@router.get("/products/{sku}", response_model=ProductOut)
def product(sku: str, repo: ProductRepository = Depends(repo_for)):
    found = repo.get(sku, public=True)
    if not found:
        raise HTTPException(404, "Product not found")
    return found


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request, repo: ProductRepository = Depends(repo_for)):
    try:
        runner = request.app.state.agent_runner or run_agent
        answer, referenced = runner(repo, payload.message, payload.history)
        return ChatResponse(answer=answer, products=referenced)
    except Exception:
        logger.exception("The product agent failed")
        raise HTTPException(
            503, "Assistant temporarily unavailable; browse the catalog instead"
        ) from None


@router.post("/admin/login", response_model=AdminIdentity)
def login(payload: AdminLogin, response: Response, db=Depends(get_db)):
    username = payload.username.strip().lower()
    if not authenticate(db, username, payload.password):
        raise HTTPException(401, "Invalid credentials")
    token, csrf = new_session(db, username, settings.admin_session_hours)
    set_session_cookie(response, token)
    response.headers["Cache-Control"] = "no-store"
    return AdminIdentity(username=username, csrf_token=csrf, role="admin")


@router.post("/auth/signup", response_model=AdminIdentity, status_code=status.HTTP_201_CREATED)
def signup(payload: AccountSignup, response: Response, db=Depends(get_db)):
    username = payload.username.strip().lower()
    if db.admin_users.find_one({"username": username}) or db.store_users.find_one(
        {"username": username}
    ):
        raise HTTPException(409, "Username is already taken")
    db.store_users.insert_one(
        {"username": username, "password_hash": hash_password(payload.password)}
    )
    token, csrf = new_session(db, username, settings.admin_session_hours, role="customer")
    set_session_cookie(response, token)
    response.headers["Cache-Control"] = "no-store"
    return AdminIdentity(username=username, csrf_token=csrf, role="customer")


@router.post("/auth/login", response_model=AdminIdentity)
def account_login(payload: AdminLogin, response: Response, db=Depends(get_db)):
    username = payload.username.strip().lower()
    role = authenticate_account(db, username, payload.password)
    if not role:
        raise HTTPException(401, "Invalid credentials")
    token, csrf = new_session(db, username, settings.admin_session_hours, role=role)
    set_session_cookie(response, token)
    response.headers["Cache-Control"] = "no-store"
    return AdminIdentity(username=username, csrf_token=csrf, role=role)


@router.get("/auth/me", response_model=AdminIdentity)
def account_me(response: Response, session=Depends(require_session)):
    response.headers["Cache-Control"] = "no-store"
    return AdminIdentity(
        username=session["username"],
        csrf_token=session["csrf_token"],
        role=session.get("role", "admin"),
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def account_logout(
    request: Request,
    response: Response,
    db=Depends(get_db),
    session=Depends(require_session_csrf),
):
    revoke_session(db, request.cookies[COOKIE_NAME])
    response.delete_cookie(COOKIE_NAME, path="/api")


@router.get("/admin/me", response_model=AdminIdentity)
def me(response: Response, session=Depends(require_admin)):
    response.headers["Cache-Control"] = "no-store"
    return AdminIdentity(
        username=session["username"], csrf_token=session["csrf_token"], role="admin"
    )


@router.post("/admin/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db=Depends(get_db),
    session=Depends(require_csrf),
):
    revoke_session(db, request.cookies[COOKIE_NAME])
    response.delete_cookie(COOKIE_NAME, path="/api")


@router.get("/admin/products", response_model=list[ProductOut])
def admin_products(repo: ProductRepository = Depends(repo_for), session=Depends(require_admin)):
    return repo.list(public=False, limit=500)


@router.post("/admin/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    repo: ProductRepository = Depends(repo_for),
    session=Depends(require_csrf),
):
    try:
        return repo.create(payload)
    except DuplicateKeyError:
        raise HTTPException(409, "SKU already exists") from None


@router.put("/admin/products/{sku}", response_model=ProductOut)
def update_product(
    sku: str,
    payload: ProductUpdate,
    repo: ProductRepository = Depends(repo_for),
    session=Depends(require_csrf),
):
    updated = repo.update(sku, payload)
    if not updated:
        raise HTTPException(404, "Product not found")
    return updated


@router.delete("/admin/products/{sku}", status_code=status.HTTP_204_NO_CONTENT)
def archive_product(
    sku: str, repo: ProductRepository = Depends(repo_for), session=Depends(require_csrf)
):
    if not repo.archive(sku):
        raise HTTPException(404, "Product not found")
