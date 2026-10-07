"""FastAPI application for the Campus Customs storefront.

Run from this folder with: uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic_ai import UsageLimits
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from agent import MODEL, shop_agent
from audit import append_event
from auth import SESSION_DAYS, authenticate_user, create_session, register_user, revoke_session, user_for_session
from db import DB_PATH, PRODUCT_IMAGES, initialize_database, read_chat_history, read_product, read_products, save_chat_exchange
from grounding import exact_product_from_message, grounded_fact_reply
from models import AuthResponse, ChatHistoryItem, ChatRequest, ChatResponse, LoginRequest, Product, RegisterRequest, ShopDeps
from tools import search_catalogue


COOKIE_NAME = "cc_session"


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Campus Customs API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.mount("/media/products", StaticFiles(directory=PRODUCT_IMAGES, check_dir=False), name="products")


def _set_session_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/",
    )


@app.get("/api/health")
def health() -> dict:
    return {"ok": DB_PATH.is_file()}


@app.get("/api/products", response_model=list[Product])
def list_products(q: str | None = Query(default=None, max_length=100)) -> list[dict]:
    products = read_products()
    if not q:
        return products
    needle = q.casefold().strip()
    return [
        product for product in products
        if needle in " ".join([
            product["name"], product["garment_type"], product["description"],
            *product["colors"], *product["search_tags"],
        ]).casefold()
    ]


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: str) -> dict:
    product = read_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/api/auth/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, request: Request, response: Response) -> dict:
    try:
        user = register_user(body.first_name, body.last_name, str(body.email), body.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _set_session_cookie(response, request, create_session(user["id"]))
    return {"user": user}


@app.post("/api/auth/login", response_model=AuthResponse)
def login(body: LoginRequest, request: Request, response: Response) -> dict:
    user = authenticate_user(str(body.email), body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    _set_session_cookie(response, request, create_session(user["id"]))
    return {"user": user}


@app.get("/api/auth/me", response_model=AuthResponse)
def me(request: Request) -> dict:
    user = user_for_session(request.cookies.get(COOKIE_NAME))
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return {"user": user}


@app.post("/api/auth/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    revoke_session(request.cookies.get(COOKIE_NAME))
    response.delete_cookie(COOKIE_NAME, path="/")


@app.get("/api/chat/history", response_model=list[ChatHistoryItem])
def chat_history(request: Request) -> list[dict]:
    user = user_for_session(request.cookies.get(COOKIE_NAME))
    if user is None:
        return []
    return read_chat_history(user["id"])


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    if MODEL is None:
        raise HTTPException(status_code=503, detail="The chat assistant needs an API key")

    user = user_for_session(request.cookies.get(COOKIE_NAME))
    page_product_id = body.page_product_id if body.page_product_id and read_product(body.page_product_id) else None
    deps = ShopDeps(
        user_id=user["id"] if user else None,
        customer_name=user["name"] if user else None,
        customer_email=user["email"] if user else None,
        page_product_id=page_product_id,
    )

    previous = read_chat_history(user["id"], limit=12) if user else []
    message_history = []
    for item in previous:
        if item["role"] == "user":
            message_history.append(ModelRequest(parts=[UserPromptPart(content=item["content"])]))
        elif item["role"] == "assistant":
            message_history.append(ModelResponse(parts=[TextPart(content=item["content"])]))

    try:
        result = await shop_agent.run(
            body.message,
            deps=deps,
            message_history=message_history,
            usage_limits=UsageLimits(request_limit=4, tool_calls_limit=8),
        )
    except Exception as exc:
        append_event("agent_run", args={"logged_in": user is not None, "page_product_id": page_product_id}, result={"error_type": type(exc).__name__}, stop_reason="model_error")
        raise HTTPException(status_code=502, detail="The shop assistant could not respond right now") from exc

    exact_product = exact_product_from_message(body.message, read_product(page_product_id) if page_product_id else None)
    products = deps.matched_products[:8]
    if not products and exact_product:
        from models import ProductCard
        products = [ProductCard.model_validate(exact_product)]
    elif not products:
        products = search_catalogue(body.message)
    guarded_reply = grounded_fact_reply(body.message, exact_product)
    response = ChatResponse(reply=guarded_reply or result.output, products=products)
    if user:
        save_chat_exchange(user["id"], body.message, response.reply, [item.model_dump() for item in response.products])
    append_event(
        "agent_run",
        args={"logged_in": user is not None, "page_product_id": page_product_id},
        result={"product_count": len(response.products), "reply_chars": len(response.reply), "fact_guard": bool(guarded_reply)},
        stop_reason="grounded_override" if guarded_reply else "completed",
    )
    return response
