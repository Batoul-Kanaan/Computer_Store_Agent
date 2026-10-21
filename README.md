# Circuit & Co. — Computer Store AI

A complete local demo for the computer-store assignment: public catalog, admin CMS, MongoDB, FastAPI, React, and a LangChain product agent. The products and store name are **fictional demo data**.

## What was adapted from the previous project

Source: [`Batoul-Kanaan/Company_AI_Assistant`](https://github.com/Batoul-Kanaan/Company_AI_Assistant), reviewed at commit `f51a9ab`.

| Previous approach | Adapted here | Reason |
| --- | --- | --- |
| FastAPI entry point, grouped routes, Pydantic models | `backend/app/main.py`, `routes.py`, `models.py` | A public catalog plus a protected admin API, with explicit response schemas. |
| PyMongo CRUD for employees/tickets | `database.py` product repository | Products replace internal records; unique SKU, search, catalog visibility, price and stock filters. |
| `@tool` functions for employee/ticket lookup | `agent.py` product search, detail and comparison tools | The agent uses live published product data. |
| Custom `bind_tools` agent loop | LangChain `create_agent` | Uses the assigned LangChain Agent API, including model-selected tool calls. |
| Chat input, message history, React/Vite structure | `frontend/src/App.jsx` and `api.js` | Customer-facing chat, catalog, product detail, and admin CMS. |
| Basic username/password and browser token | Admin-only PBKDF2 login, Mongo-backed session, HttpOnly cookie, CSRF token | Removes public signup and keeps the session token out of JavaScript/localStorage. |
| Qdrant and PDF chunks | Deferred | Structured products already live in MongoDB. Add RAG only if manuals, support articles, or large FAQ documents become requirements. |

No old employee records, tickets, internal documents, secrets, or database content were copied. The implementation applies useful patterns to a new domain.

## Stack and architecture

- **Python / FastAPI / Pydantic:** validated REST API.
- **MongoDB / PyMongo:** product, admin user, and expiring admin session collections.
- **LangChain / langchain-ollama / Ollama:** `create_agent` and three read-only catalog tools. The default model is `qwen3:4b-instruct`; choose another Ollama model with tool calling through `.env` if your hardware needs it.
- **React / Vite / React Router:** responsive customer catalog, product details, admin forms, chat, and separate page routes.
- **pytest / mongomock / FastAPI TestClient:** backend behavior without live external services.

The product collection is the single source of truth. The customer API and agent only read `status=published`; the admin API can see drafts and archived items. `DELETE` archives a product rather than removing it. The agent has no write tools.

## Run locally (Windows PowerShell)

Prerequisites: Python 3.11+, Node.js 20.19+ or 22.12+, Docker Desktop for MongoDB (or a local MongoDB server), and [Ollama](https://ollama.com/download). Use three PowerShell windows. Commands run from this project root unless stated otherwise.

```powershell
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
docker compose up -d mongo
ollama pull qwen3:4b-instruct
python -m backend.scripts.seed
python -m backend.scripts.create_admin --username admin
python -m uvicorn backend.app.main:app --reload
```

The admin command asks for a password (minimum 12 characters) and confirmation. It rotates the password and revokes old sessions if run for an existing username. It never prints or stores the plaintext password. If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` for each Python command instead.

In the second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. The Vite dev server proxies `/api` to FastAPI at `127.0.0.1:8000`, so cookies work under one browser origin. FastAPI interactive docs: `http://127.0.0.1:8000/docs`. The demo inventory includes a draft and an out-of-stock laptop for visibility tests. Rerunning seed inserts missing SKUs only and preserves admin edits.

The storefront opens with sign-in, account creation, or guest access. Customer accounts can browse the same public catalog; only authenticated admin accounts see the Admin navigation link. Open `http://127.0.0.1:5173/admin` directly for the separate management page; the API enforces the admin role and CSRF checks regardless of navigation visibility. The management UI is loaded as a separate JavaScript chunk. For production hosting, configure SPA fallback to `index.html` for frontend routes such as `/admin`, while forwarding `/api` requests to FastAPI.

### VS Code / Pylance says a LangChain import is missing

Open the **inner `computer-store-ai` directory containing `requirements.txt`** as the VS Code workspace. ZIP extraction can produce `computer-store-ai/computer-store-ai`; run the following from the inner directory. You do not need to activate PowerShell scripts:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "from langchain.agents import create_agent; from langchain.tools import tool; from langchain_core.messages import ToolMessage; from langchain_ollama import ChatOllama; print('Imports OK')"
```

In VS Code press **Ctrl+Shift+P → Python: Select Interpreter → Enter interpreter path** and choose the inner project's `.venv\Scripts\python.exe`. If the imports succeed in the terminal but Pylance still shows warnings, use **Developer: Reload Window**. Installing packages into one Python interpreter does not make them visible to a different interpreter selected in VS Code.

On macOS/Linux use `python3 -m venv .venv`, `source .venv/bin/activate`, and `cp .env.example .env`; remaining commands are the same. If not using Docker, configure `MONGO_URI` in `.env` and start MongoDB yourself. If the browser/API run at another origin or behind HTTPS, set `FRONTEND_ORIGIN` and `COOKIE_SECURE=true` as appropriate; serve the UI and API under one origin or update the deployment proxy.

## API map

| Method and path | Access | Purpose |
| --- | --- | --- |
| `GET /api/health` | Public | MongoDB readiness ping. |
| `GET /api/products` | Public | Search/filter published products: `query`, `category`, `brand`, `max_price_cents`, `in_stock`. |
| `GET /api/products/{sku}` | Public | Published product detail. Draft/archived returns 404. |
| `POST /api/chat` | Public | `{ "message": "...", "history": [{"role":"user","content":"..."}] }` → answer and product references. |
| `POST /api/auth/signup` | Public | Create a customer account and start a session. |
| `POST /api/auth/login` | Public | Sign in a customer or admin account. |
| `GET /api/auth/me` | Session cookie | Restore the current account and role. |
| `POST /api/auth/logout` | Cookie + `X-CSRF-Token` | Revoke the current account session. |
| `POST /api/admin/login` | Public | Admin credentials → HttpOnly cookie plus CSRF token. |
| `GET /api/admin/me` | Admin session cookie or Bearer token | Restore admin identity and CSRF token after refresh. |
| `POST /api/admin/logout` | Admin session cookie or Bearer token + `X-CSRF-Token` | Revoke session. |
| `GET /api/admin/products` | Admin session cookie or Bearer token | All product statuses. |
| `POST /api/admin/products` | Admin session cookie or Bearer token + `X-CSRF-Token` | Create a product. |
| `PUT /api/admin/products/{sku}` | Admin session cookie or Bearer token + `X-CSRF-Token` | Replace editable fields; SKU is immutable. |
| `DELETE /api/admin/products/{sku}` | Admin session cookie or Bearer token + `X-CSRF-Token` | Archive a product. |

For API clients, send the session value from the `store_admin` login cookie as `Authorization: Bearer <token>`. Admin writes still require the CSRF token returned by login in `X-CSRF-Token`.

Product fields: `sku`, `name`, `brand`, `category` (`laptop`, `component`, `electronic`), `description`, `price_cents`, `stock_quantity`, optional `image_url`, `specifications` (name/value strings), and `status` (`draft`, `published`, `archived`). The API also returns `created_at`, `updated_at`. Prices are stored as integer USD cents to avoid floating point rounding in the database. SKU is a unique stock keeping unit, not a MongoDB ObjectId.

## Agent behavior

`make_product_tools()` builds `search_products`, `get_product_details`, and `compare_products` over the same repository as the REST API. `run_agent()` constructs a LangChain `create_agent` using Ollama, supplies the last eight turns, limits graph recursion, extracts referenced SKUs from tool output, and re-reads public records before returning product cards. A response with no catalog tool use becomes a safe request to rephrase. Product details, price, and stock can change between questions; there is no checkout or stock reservation.

Try these review prompts after starting the services:

1. “Which in-stock laptop is under $900?” → Orbit 14, not the out-of-stock Cloud 13.
2. “Compare Orbit 14 and Orbit Pro 16. What differs?” → real SKU, price, RAM, GPU and display differences.
3. “What AM5 CPU and motherboard do you have?” → Ryzen 5 7600 and Atlas B650 WiFi.
4. “Can I buy LAP-FUTURE-17?” → draft must be unavailable to the agent and public API.
5. Change a price or stock number in Admin; ask again → agent should use current database values.
6. Ask a compatibility question unsupported by stored specs → agent should state what needs checking, not guarantee compatibility.

Tool quality depends on the local model. The automated tests validate data visibility, CRUD/auth, and tool results without loading model weights; they do **not** prove that Ollama's generated answers are always correct. Run the six prompts above against a live Ollama instance before a presentation. If the model misses tool calls, try a stronger tool-capable model in `.env` and evaluate again. No embeddings or Qdrant are required for structured inventory; add a separate document ingestion and retrieval tool if manuals become part of the scope.

## Tests and production notes

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check backend tests
python -m ruff format --check backend tests
cd frontend
npm ci
npm run build
npm run format:check
```

Admin cookies are HttpOnly/SameSite=Lax and admin writes require the CSRF header. Session hashes are stored in MongoDB with a TTL index; expired sessions are rejected even before MongoDB's TTL cleanup. Use HTTPS and `COOKIE_SECURE=true` outside local development. The demo has no rate limiting, image uploads, payment flow, commerce inventory reservation, distributed chat memory, or production deployment configuration. Add those as separate tasks if needed.

## File guide

| File | Role |
| --- | --- |
| `backend/app/config.py` | Environment-backed Mongo, Ollama, and cookie settings. |
| `backend/app/models.py` | Product, chat, and admin request/response validation. |
| `backend/app/database.py` | MongoDB startup/indexes, public/admin product repository and search. |
| `backend/app/auth.py` | Password hashing, sessions, cookie and CSRF dependencies. |
| `backend/app/agent.py` | LangChain Agent prompt, product tools and invocation. |
| `backend/app/routes.py` | REST endpoints and access control. |
| `backend/app/main.py` | FastAPI app, lifespan, CORS. |
| `backend/scripts/seed.py` | Idempotent fictional inventory. |
| `backend/scripts/create_admin.py` | Interactive admin bootstrap/password rotation. |
| `frontend/src/api.js` | Browser API requests and error handling. |
| `frontend/src/App.jsx` | Customer/admin route selection and unknown-page view. |
| `frontend/src/pages/Storefront.jsx` | Account entry, guest access, catalog, filters, product details, chat and admin-only navigation. |
| `frontend/src/pages/AdminPage.jsx` | Separate management shell for `/admin`, loaded on demand. |
| `frontend/src/components/Product.jsx` | Product cards, fallback art and detail view. |
| `frontend/src/components/Chat.jsx` | Conversation, suggestions and product references. |
| `frontend/src/components/Admin.jsx` | Admin login, inventory and product editor. |
| `frontend/src/lib/product.js` | Category names and USD formatting. |
| `frontend/src/styles.css` | Responsive UI. |
| `tests/` | Backend contract and behavior tests. |

#   C o m p u t e r _ S t o r e _ A g e n t  
 