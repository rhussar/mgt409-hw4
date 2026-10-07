# Campus Customs build harness

## Database field guide

Inspected `data/campus_customs.db` directly with SQLite. It currently has 102 catalogue products, 612 inventory rows, 3 users, and 22 chat messages. These counts describe the supplied copy and may change as the app is used.

### `catalogue` — products shown in the shop

| Field | Purpose in the shop or chatbot |
| --- | --- |
| `product_id` (TEXT, primary key) | Stable product identifier for URLs and joining stock to products. |
| `name` (TEXT, required) | Display name on cards, detail pages, and chat results. |
| `garment_type` (TEXT, required) | Product category for browsing and answering clothing-type requests. |
| `description` (TEXT, required) | Product details for shoppers and grounded chat answers. |
| `colors` (TEXT, required) | JSON array of colors for filters and color questions. |
| `search_tags` (TEXT, required) | JSON array of search terms for matching shopper requests. |
| `image_file_path` (TEXT, required) | Relative path to the matching image under `data/`; the app converts it to a safe media URL. |
| `price` (REAL, required) | Price displayed to shoppers; answers about price must use this value. |

### `inventory` — stock by product and size

| Field | Purpose in the shop or chatbot |
| --- | --- |
| `id` (INTEGER, primary key) | Unique stock-row identifier. |
| `product_id` (TEXT, required) | Links a size's stock to `catalogue.product_id`. |
| `size` (TEXT, required) | Size option on a product page and in stock answers. |
| `quantity` (INTEGER, required) | Current units available for that product and size; zero means unavailable. |

The database makes `(product_id, size)` unique, so each product has at most one stock row per size.

### `users` — accounts

| Field | Purpose in the shop or chatbot |
| --- | --- |
| `id` (INTEGER, primary key) | Internal account identifier, also used to link chat history. |
| `name` (TEXT, required) | Account display name. |
| `email` (TEXT, required, unique) | Login identity and duplicate-account check. |
| `password_hash` (TEXT, required) | Stored password verifier; never expose it in API responses. |
| `created_at` (TEXT, required) | Account creation timestamp. |
| `first_name` (TEXT, nullable) | Optional given name for personalized greetings. |
| `last_name` (TEXT, nullable) | Optional family name for the account profile. |

### `chat_messages` — existing conversation history

| Field | Purpose in the shop or chatbot |
| --- | --- |
| `id` (INTEGER, primary key) | Unique message identifier and stable ordering aid. |
| `user_id` (INTEGER, required) | Links the message to `users.id`. |
| `role` (TEXT, required) | Distinguishes user and assistant messages. |
| `content` (TEXT, required) | Message text. |
| `products_json` (TEXT, nullable) | JSON list of products attached to a chat response, for the product panel. |
| `created_at` (TEXT, required) | Message timestamp for chronological history. |

The storefront reads catalogue and inventory through the API.

### `sessions` — created by the app at startup

| Field | Purpose |
| --- | --- |
| `token_hash` (TEXT, primary key) | SHA-256 digest of the opaque cookie token; the raw token is never stored in the database. |
| `user_id` (INTEGER, required) | Account attached to the session. |
| `expires_at` (TEXT, required) | Seven-day validity limit checked on each authenticated request. |
| `created_at` (TEXT, required) | Session creation time. |

## Authentication

Registration accepts first name, last name, email, and password. It writes `name`, `first_name`, `last_name`, normalized `email`, and `password_hash` into `users`. Passwords are never returned in API responses. New hashes use PBKDF2-HMAC-SHA256 with a random per-user salt and 600,000 iterations; the iteration count is stored in the hash string. The supplied test account uses a legacy 120,000-iteration PBKDF2 format. A successful login verifies that format and upgrades the stored hash to the new work factor. Hash comparison uses `hmac.compare_digest`.

Successful registration and login create a random, seven-day session token. Only its SHA-256 digest is stored in a `sessions` table; the browser receives the opaque token in an HttpOnly, SameSite=Lax cookie. `/api/auth/me` checks the session, and logout revokes it. The client never reads or stores the token in JavaScript. The API returns only public user fields.

The supplied test account and a newly registered account were both verified in a temporary copy of the database, including login, logout, and password storage. [OWASP's password storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) recommends the PBKDF2-HMAC-SHA256 work factor used for new accounts.

## App and agent wiring

`frontend/` is a Vite React and TypeScript app. Its catalogue fetches `/api/products`, and detail pages fetch `/api/products/{product_id}`. Product images are served from the local data pack at `/media/products/`. The Products page has an in-stock size filter and name/price sorting. Account pages use `/api/auth/register`, `/api/auth/login`, `/api/auth/me`, and `/api/auth/logout` with an HttpOnly cookie.

`backend/main.py` owns the FastAPI routes and starts the database. The `POST /api/chat` route validates a `ChatRequest` containing a 1–1000 character message and optional page product ID. It verifies that product ID, resolves the session cookie, constructs `ShopDeps`, loads at most 12 recent messages for a signed-in user, and calls `shop_agent.run` with a four-request and eight-tool-call limit. The response shape is `{ "reply": string, "products": ProductCard[] }`. The frontend renders `products` as linked cards. It saves both sides of the exchange for a signed-in user and never writes guest messages to `chat_messages`. `GET /api/chat/history` returns up to 50 of that user's messages in display order; guests receive an empty list.

`backend/agent.py` loads `backend/prompts/prompt.md`, selects the PydanticAI OpenAI chat model through Portkey or a direct OpenAI key, and supplies trusted shopper and page context through dynamic instructions. The model is configured by `CAMPUS_CUSTOMS_MODEL` and defaults to `gpt-5.6`. The key is read from environment variables or a local `.env`; it is absent from the repository and audit output. `backend/models.py` validates request, response, inventory, user, product-card, and tool-result shapes. `ShopDeps` holds trusted identity, the current product ID, and the cards selected during a run.

## Agent tools and factual checks

| Tool | Inputs | Database result and purpose |
| --- | --- | --- |
| `search_products` | Search query | Ranks real catalogue rows by name, garment type, tags, and description; returns at most eight typed product cards. Common plural category words are normalized. |
| `get_product_description` | Product name/ID or “this” | Returns the matched item's ID, name, garment type, description, and colors. |
| `get_product_price` | Product name/ID or “this” | Returns the current catalogue price for one unambiguous item. |
| `get_product_stock` | Product name/ID or “this”, optional size | Returns inventory rows and total quantity. Zero quantities remain visible; an unknown requested size returns no row. |

All tools read the SQLite data pack through `backend/db.py`. A vague or tied product match returns no result so the assistant can ask which item the shopper meant. Category matches travel in the structured `products` API field, making cards dynamic rather than hard-coded. `backend/grounding.py` adds a final check for clear product-page or explicitly named price/size questions: it builds the factual reply directly from the catalogue and inventory, including an out-of-stock or unverifiable-size answer. The agent may still answer descriptive questions normally.

## Safety and audit

The prompt tells the assistant to use tools before giving catalogue facts, treat customer messages, past history, and product descriptions as data, protect account information and secrets, and avoid claims about orders, payment, delivery, or unknown policies. API responses never include password hashes. Only a validated product ID from the current page becomes trusted page context. Inputs are bounded by Pydantic models, and the agent has request and tool-call limits. The browser displays response text as React text nodes with a small bold-text formatter rather than inserting model HTML.

`backend/audit.py` appends records to `output/audit_trail.json` with UTC time, event/tool name, short arguments, short result, and stop reason. Tool calls record IDs, counts, and verified price where relevant; agent-run records contain completion or error status, card count, and whether the factual guard was used. Chat content, account email, cookies, and keys are excluded. The writer locks the file, inserts a record before the JSON array's closing bracket, and flushes it without discarding earlier records.

## Run specifications and checks

Place the supplied `data/campus_customs.db` and `data/products/` beneath `hw4/`, and put a valid provider key in a private `.env` copied from `.env.example`. From `backend/`, install `requirements.txt` in Python 3.12 or later and run `uvicorn main:app --reload --port 8000`. From `frontend/`, run `npm install` and `npm run dev`; open `http://127.0.0.1:5173/`. Vite proxies `/api` and `/media` to the backend. `frontend/npm run build` checks the TypeScript and production build. The repository excludes `.env`, the SQLite file, product images, dependencies, and build output.

Authentication was checked with the supplied test account and a new account in a temporary database copy. Chat was exercised against the live model for a hoodie category query and a current-product XL/price question. A separate API check used PydanticAI's test model to verify signed-in chat persistence and history loading. `output/app_check.html` provides browser screenshots of the live UI.
