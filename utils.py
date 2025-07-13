"""Utility functions for AI chat back‑end."""

import os

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def get_ai_response(history: list[dict], prompt: str) -> str:
    """Return assistant response given conversation history and the latest user prompt.

    Parameters
    ----------
    history : list[dict]
        Previous messages excluding the new prompt, each like {"role": "user"|"assistant", "content": "..."}
    prompt : str
        New user message
    """
    # Demo fallback when SDK not installed or API key missing
    if not OPENAI_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        return f"(demo) Echo: {prompt}"

    client = OpenAI()
    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history + [{"role": "user", "content": prompt}],
    )
    return chat_completion.choices[0].message.content
