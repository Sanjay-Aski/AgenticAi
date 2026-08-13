"""Deterministic tutoring agent with controlled input-output contracts."""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from config import (
    DEFAULT_FALLBACK_RESPONSE,
    ENABLE_GUARDRAILS,
    GUARDRAIL_RESPONSE,
    MAX_INPUT_LENGTH,
)
from logger import InteractionLogger


@dataclass(frozen=True)
class TutorRequest:
    question: str


@dataclass(frozen=True)
class TutorResponse:
    intent: str
    version: str
    response_text: str
    guardrail_triggered: bool
    response_time_ms: float


class DeterministicTutorAgent:
    def __init__(self, templates_path: Path, logger: InteractionLogger) -> None:
        self.templates_path = templates_path
        self.logger = logger
        self._templates = self._load_templates(templates_path)
        self._fallback = self._templates.get("default_response", DEFAULT_FALLBACK_RESPONSE)
        self._topics = sorted(
            self._templates["topics"], key=lambda t: int(t.get("priority", 999))
        )

        for topic in self._topics:
            self.logger.upsert_response_version(
                topic["intent"], topic.get("version", "v1"), topic["response"]
            )

    def _load_templates(self, path: Path) -> Dict:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s-]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _input_hash(normalized_text: str) -> str:
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    @staticmethod
    def _guardrail_check(normalized_text: str) -> bool:
        blocked_patterns = [
            "ignore previous",
            "reveal system prompt",
            "jailbreak",
            "developer mode",
            "bypass",
            "drop table",
            "delete from",
            "<script",
            "union select",
        ]
        return any(pattern in normalized_text for pattern in blocked_patterns)

    def _detect_intent(self, normalized_text: str) -> Tuple[str, str, str]:
        best_score = 0
        best_topic = None

        for topic in self._topics:
            keywords: List[str] = topic.get("keywords", [])
            score = sum(1 for kw in keywords if kw in normalized_text)
            if score > best_score:
                best_score = score
                best_topic = topic

        if best_topic and best_score > 0:
            return (
                best_topic["intent"],
                best_topic.get("version", "v1"),
                best_topic["response"],
            )

        return ("unknown", "v1", self._fallback)

    def answer(self, req: TutorRequest) -> TutorResponse:
        start = time.perf_counter()
        raw_question = (req.question or "").strip()
        safe_question = raw_question[:MAX_INPUT_LENGTH]
        normalized = self.normalize(safe_question)

        guardrail_triggered = ENABLE_GUARDRAILS and self._guardrail_check(normalized)
        if guardrail_triggered:
            intent, version, response_text = "guardrail_blocked", "v1", GUARDRAIL_RESPONSE
        elif not normalized:
            intent, version, response_text = "empty", "v1", self._fallback
        else:
            intent, version, response_text = self._detect_intent(normalized)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)

        payload = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "question": raw_question,
            "normalized_question": normalized,
            "input_hash": self._input_hash(normalized),
            "detected_intent": intent,
            "response_version": version,
            "response_text": response_text,
            "response_time_ms": elapsed_ms,
            "guardrail_triggered": guardrail_triggered,
        }
        self.logger.log_interaction(payload)

        return TutorResponse(
            intent=intent,
            version=version,
            response_text=response_text,
            guardrail_triggered=guardrail_triggered,
            response_time_ms=elapsed_ms,
        )
