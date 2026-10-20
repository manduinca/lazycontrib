from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

BASE_URL = os.environ.get("LAZYCONTRIB_LLM_URL", "http://localhost:11434")
MODEL = os.environ.get("LAZYCONTRIB_MODEL", "gemma4:e4b")
API_KEY = os.environ.get("LAZYCONTRIB_LLM_KEY", "")
CONTEXT = int(os.environ.get("LAZYCONTRIB_CONTEXT", "16384"))
MAX_REPAIRS = 2


class LLMError(RuntimeError):
    pass


def _ollama() -> bool:
    return ":11434" in BASE_URL or os.environ.get("LAZYCONTRIB_LLM_API", "").lower() == "ollama"


def chat(messages: list[dict[str, str]], schema: dict[str, Any] | None = None, timeout: float = 300) -> str:
    """One completion from a local Ollama server or any OpenAI-compatible endpoint."""
    with httpx.Client(timeout=timeout) as client:
        if _ollama():
            body = {"model": MODEL, "messages": messages, "stream": False, "think": False,
                    "options": {"temperature": 0.1, "num_ctx": CONTEXT, "num_predict": 2048}}
            if schema is not None:
                body["format"] = schema
            response = client.post(f"{BASE_URL.rstrip('/')}/api/chat", json=body)
            if response.status_code >= 400:
                raise LLMError(f"ollama returned {response.status_code}: {response.text[:300]}")
            return response.json()["message"]["content"]
        body = {"model": MODEL, "messages": messages, "temperature": 0.1}
        if schema is not None:
            body["response_format"] = {"type": "json_schema", "json_schema": {"name": "reply", "schema": schema}}
        headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
        response = client.post(f"{BASE_URL.rstrip('/')}/chat/completions", json=body, headers=headers)
        if response.status_code >= 400 and schema is not None:
            body["response_format"] = {"type": "json_object"}
            response = client.post(f"{BASE_URL.rstrip('/')}/chat/completions", json=body, headers=headers)
        if response.status_code >= 400:
            raise LLMError(f"endpoint returned {response.status_code}: {response.text[:300]}")
        return response.json()["choices"][0]["message"]["content"]


def _json(text: str) -> Any:
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        text = fenced.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("the reply has no JSON object")
    return json.loads(text[start:end + 1])


def structured(system: str, user: str, model_cls: type[BaseModel]) -> tuple[Any, int]:
    """Ask for JSON matching model_cls; send validation errors back up to MAX_REPAIRS times."""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    schema = model_cls.model_json_schema()
    for attempt in range(MAX_REPAIRS + 1):
        reply = chat(messages, schema)
        try:
            return model_cls.model_validate(_json(reply)), attempt + 1
        except (ValidationError, ValueError) as error:
            problems = [f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in error.errors()][:8] \
                if isinstance(error, ValidationError) else [str(error)]
            messages += [{"role": "assistant", "content": reply},
                         {"role": "user", "content": "That JSON was rejected:\n- " + "\n- ".join(problems)
                          + "\nReturn the corrected JSON only."}]
    raise LLMError(f"no valid reply after {MAX_REPAIRS + 1} attempts")


def _squash(text: str) -> str:
    text = re.sub(r"[`*_>#\[\]()]", " ", text.lower())
    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    return " ".join(text.split())


def grounded(quote: str, *sources: str) -> bool:
    """True when the quote really appears in one of the sources, ignoring case, markdown and spacing."""
    needle = _squash(quote).strip(" .,:;\"'")
    if len(needle) < 8:
        return False
    return any(needle in _squash(source) for source in sources)
