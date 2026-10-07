"""PydanticAI shop assistant wiring and model configuration."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from db import PROJECT_ROOT
from models import ShopDeps
from tools import register_tools


load_dotenv(PROJECT_ROOT / ".env")
if not os.getenv("PORTKEY_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    load_dotenv(PROJECT_ROOT.parent / ".env")

PROMPT_PATH = Path(__file__).parent / "prompts" / "prompt.md"
MODEL_NAME = os.getenv("CAMPUS_CUSTOMS_MODEL", "gpt-5.6")


def _model() -> OpenAIChatModel | None:
    portkey_key = os.getenv("PORTKEY_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if portkey_key:
        client = AsyncOpenAI(
            api_key=portkey_key,
            base_url="https://api.portkey.ai/v1",
            default_headers={"x-portkey-api-key": portkey_key, "x-portkey-provider": "openai"},
            max_retries=0,
            timeout=30,
        )
    elif openai_key:
        client = AsyncOpenAI(api_key=openai_key, max_retries=0, timeout=30)
    else:
        return None
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


MODEL = _model()
shop_agent = register_tools(
    Agent(
        MODEL if MODEL is not None else "test",
        deps_type=ShopDeps,
        output_type=str,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
    )
)


@shop_agent.instructions
def shopper_context(ctx: RunContext[ShopDeps]) -> str:
    """Add trusted identity and page state without putting it in the user message."""
    if ctx.deps.user_id is None:
        identity = "The shopper is a guest."
    else:
        identity = f"The logged-in shopper is {ctx.deps.customer_name} (email: {ctx.deps.customer_email})."
    page = f"Current product page: {ctx.deps.page_product_id}." if ctx.deps.page_product_id else "The shopper is not on a product detail page."
    return identity + " " + page
