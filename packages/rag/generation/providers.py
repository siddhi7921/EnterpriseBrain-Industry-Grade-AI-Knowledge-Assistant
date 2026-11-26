from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, List



@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        raise NotImplementedError

    def count_tokens(self, text: str) -> int:
        return max(1, int(round(len(text.split()) * 1.3))) if text else 0


class OpenAICompatibleProvider(BaseLLMProvider):
    """Supports OpenAI, Azure OpenAI, Groq, OpenRouter, vLLM, and Ollama /v1/chat/completions endpoints."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or "ollama"
        self.model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        import httpx

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        in_tok = usage.get("prompt_tokens", self.count_tokens(system_prompt + user_prompt))
        out_tok = usage.get("completion_tokens", self.count_tokens(content))
        return LLMResponse(
            content=content,
            model=self.model,
            input_tokens=int(in_tok),
            output_tokens=int(out_tok),
        )

    async def stream(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        import httpx

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        chunk = json.loads(raw)
                        delta = chunk["choices"][0].get("delta", {}).get("content", "")
                        if delta:
                            yield delta
                    except Exception:
                        continue


class GroundedExtractiveFallbackProvider(BaseLLMProvider):
    """Zero-API-key deterministic grounded synthesizer for offline demos, local dev, and automated testing."""

    def __init__(self, model: str = "enterprisebrain-grounded-synthesizer-v1") -> None:
        self.model = model

    def _synthesize(self, user_prompt: str) -> str:
        if "NO_EVIDENCE_RETRIEVED" in user_prompt:
            return (
                "I could not find sufficient authorized evidence in your organisation's knowledge base "
                "to answer this question reliably."
            )

        evidence_blocks = re.findall(
            r"--- EVIDENCE \d+ \| chunk_id=([^\s|]+) \| file=([^|]+) \| page=([^|]+) \| section=([^\n-]+) ---\n(.*?)(?=\n\n--- EVIDENCE|\n\nUSER QUESTION:)",
            user_prompt,
            flags=re.DOTALL,
        )
        question_match = re.search(r"USER QUESTION:\n(.*?)\n\nReturn a concise", user_prompt, flags=re.DOTALL)
        question = question_match.group(1).strip() if question_match else ""
        q_terms = set(re.findall(r"[a-z0-9]{3,}", question.lower()))

        if not evidence_blocks:
            return (
                "I could not find sufficient authorized evidence in your organisation's knowledge base "
                "to answer this question reliably."
            )

        selected_points: List[str] = []
        for chunk_id, _filename, _page, _section, body in evidence_blocks[:3]:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body.strip()) if s.strip()]
            best_sent = sentences[0] if sentences else body.strip()[:240]
            if q_terms and sentences:
                best_sent = max(
                    sentences,
                    key=lambda s: len(q_terms & set(re.findall(r"[a-z0-9]{3,}", s.lower()))),
                )
            selected_points.append(f"- {best_sent} [CHUNK:{chunk_id.strip()}]")

        return (
            "Based on the retrieved organisation documents, here is the verified answer:\n\n"
            + "\n".join(selected_points)
        )

    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        answer = self._synthesize(user_prompt)
        return LLMResponse(
            content=answer,
            model=self.model,
            input_tokens=self.count_tokens(system_prompt + user_prompt),
            output_tokens=self.count_tokens(answer),
        )

    async def stream(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        answer = self._synthesize(user_prompt)
        for token in answer.split(" "):
            yield token + " "


def get_llm_provider(
    provider: str = "extractive_fallback",
    base_url: str = "https://api.openai.com/v1",
    api_key: str = "",
    model: str = "gpt-4o-mini",
) -> BaseLLMProvider:
    if provider == "openai_compatible" and (api_key or "localhost" in base_url or "11434" in base_url):
        return OpenAICompatibleProvider(base_url=base_url, api_key=api_key, model=model)
    return GroundedExtractiveFallbackProvider()
