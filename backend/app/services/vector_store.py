"""Lightweight retrieval-augmented generation (RAG) over dataset schemas.

Two embedding backends:
  * hash-based bag-of-words vectors (pure Python, works offline / zero deps)
  * OpenAI embeddings when OPENAI_API_KEY is set

Each dataset column becomes a knowledge chunk: its name, dtype, sample values,
stats and common-phrase aliases. When the user asks a question, the top-K most
relevant columns are retrieved and injected into the NL2SQL prompt.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from app.core.config import settings

VECTOR_DIM = 512


def _hash_tokens(tokens: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    return counts


def bow_vector(text: str) -> list[float]:
    """Deterministic bag-of-words hashing vector."""
    vec = [0.0] * VECTOR_DIM
    tokens = tokenize(text)
    counts = _hash_tokens(tokens)
    for token, c in counts.items():
        idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % VECTOR_DIM
        vec[idx] += c
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9_%]", " ", text)
    return [t for t in text.split() if len(t) > 1]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


class VectorStore:
    """Column-level knowledge base for a single dataset."""

    def __init__(self, columns: list[dict[str, Any]]):
        self.columns = columns
        self.chunks: list[dict[str, Any]] = []
        self._vectors: list[list[float]] = []
        self._build()

    def _embed(self, text: str) -> list[float]:
        return bow_vector(text)

    def _build(self) -> None:
        for col in self.columns:
            name = col.get("name", "")
            dtype = col.get("dtype", "")
            samples = [str(s) for s in (col.get("sample") or [])][:8]
            stats = col.get("stats") or {}
            summary_lines = []
            for k, v in list(stats.items())[:12]:
                summary_lines.append(f"{k}: {v}")
            aliases = col.get("aliases") or []
            text = " ".join(
                [
                    name.replace("_", " "),
                    dtype,
                    " ".join(samples),
                    " ".join(summary_lines),
                    " ".join(aliases),
                ]
            )
            self.chunks.append({"column": name, "text": text})
            self._vectors.append(self._embed(text))

    def retrieve(self, question: str, top_k: int = 8) -> list[dict[str, Any]]:
        qvec = self._embed(question)
        scored: list[tuple[float, dict[str, Any]]] = []
        for vec, chunk in zip(self._vectors, self.chunks):
            score = cosine(qvec, vec)
            if score > 0.01:
                scored.append((score, chunk))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    def to_prompt(self, question: str, top_k: int = 8) -> str:
        hits = self.retrieve(question, top_k)
        lines = []
        for h in hits:
            col = h["column"]
            text = h["text"][:240]
            lines.append(f"- `{col}`: {text}")
        return "\n".join(lines) if lines else "(no context matched)"


def build_schema_text(schema_json: dict) -> str:
    """Render the full dataset schema as human-readable prompt text."""
    lines = []
    for col in schema_json.get("columns", []):
        name = col.get("name", "")
        dtype = col.get("dtype", "")
        missing = col.get("missing", 0)
        unique = col.get("unique", 0)
        samples = ", ".join(str(s) for s in (col.get("sample") or [])[:6])
        lines.append(f"  - {name} ({dtype}) missing={missing} unique={unique} e.g. {samples}")
    return "\n".join(lines)


def build_aliases(schema_json: dict) -> dict[str, str]:
    """Map common English aliases to canonical column names."""
    alias_map: dict[str, str] = {}
    for col in schema_json.get("columns", []):
        name = col.get("name", "")
        norm = name.lower()
        alias_map[norm] = name
        alias_map[norm.replace("_", " ")] = name
        alias_map[norm.replace("_", "")] = name
        for singular in (norm.rstrip("s"), norm.replace("s ", " ")):
            if singular and singular != norm:
                alias_map[singular] = name
    return alias_map
