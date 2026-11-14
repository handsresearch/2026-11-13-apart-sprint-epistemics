"""Smoke-test API keys with one tiny call per provider (well under $0.01 total).

  source scripts/env.sh && python scripts/check_keys.py
"""

from __future__ import annotations

import asyncio
import os

from inspect_ai.model import GenerateConfig, get_model

CHECKS = {
    "ANTHROPIC_API_KEY": "anthropic/claude-haiku-5-5",
    "OPENROUTER_API_KEY": "openrouter/openai/gpt-5.6-luna",
}


async def main() -> None:
    for var, model in CHECKS.items():
        if not os.environ.get(var):
            print(f"SKIP {model}: {var} not set")
            continue
        try:
            out = await get_model(model).generate(
                "Reply with the single word: ok", config=GenerateConfig(max_tokens=5, temperature=0)
            )
            u = out.usage
            print(f"OK   {model}: {out.completion.strip()!r} (tokens in={u.input_tokens if u else '?'}, out={u.output_tokens if u else '?'})")
        except Exception as ex:  # noqa: BLE001 - report any provider error
            print(f"FAIL {model}: {type(ex).__name__}: {str(ex)[:200]}")


if __name__ == "__main__":
    asyncio.run(main())
