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
from prompts import INTENT_PROMPTS, LEVEL_GUIDANCE, SYSTEM_PROMPT


@dataclass(frozen=True)
class TutorRequest:
    question: str
    level: str = "Beginner"


@dataclass(frozen=True)
class TutorResponse:
    intent: str
    learning_intent: str
    version: str
    response_text: str
    applied_prompt: str
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

    @classmethod
    def _contains_keyword(cls, normalized_text: str, keyword: str) -> bool:
        kw = cls.normalize(keyword)
        if not kw:
            return False
        pattern = rf"(^|\s){re.escape(kw)}(\s|$)"
        return re.search(pattern, normalized_text) is not None

    def _detect_intent(self, normalized_text: str) -> Tuple[str, str, str]:
        best_score = 0
        best_topic = None

        for topic in self._topics:
            keywords: List[str] = topic.get("keywords", [])
            score = sum(1 for kw in keywords if self._contains_keyword(normalized_text, kw))
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

    @staticmethod
    def _detect_learning_intent(normalized_text: str) -> str:
        intent_rules = [
            ("comparison", ["compare", "difference", "vs", "versus"]),
            ("complexity_analysis", ["complexity", "big o", "time complexity", "space complexity"]),
            ("algorithm", ["algorithm", "steps", "procedure", "how to"]),
            ("example", ["example", "sample"]),
            ("code_generation", ["code", "program", "implement", "python", "java", "c++"]),
            ("debugging", ["debug", "error", "bug", "fix", "traceback"]),
            ("definition", ["define", "what is", "meaning"]),
        ]

        for label, keywords in intent_rules:
            if any(k in normalized_text for k in keywords):
                return label
        return "definition"

    def _format_by_level(self, base_response: str, level: str, learning_intent: str) -> str:
        safe_level = level if level in LEVEL_GUIDANCE else "Beginner"

        if "not present in the dataset" in base_response.lower() or base_response == GUARDRAIL_RESPONSE:
            return base_response

        if safe_level == "Beginner":
            return f"Topic: {learning_intent}\nAnswer: {base_response}"

        if safe_level == "Intermediate":
            return (
                f"Topic: {learning_intent}\n"
                f"Answer: {base_response}\n"
                "Summary: Use this scheme according to your need and eligibility."
            )

        return (
            f"Topic: {learning_intent}\n"
            f"Answer: {base_response}\n"
            "Summary: Verify eligibility, benefit cadence, and official enrollment channel before applying."
        )

    def answer(self, req: TutorRequest) -> TutorResponse:
        start = time.perf_counter()
        raw_question = (req.question or "").strip()
        safe_question = raw_question[:MAX_INPUT_LENGTH]
        normalized = self.normalize(safe_question)
        learning_intent = self._detect_learning_intent(normalized) if normalized else "unknown"
        applied_prompt = (
            f"{SYSTEM_PROMPT} | IntentRule: {INTENT_PROMPTS.get(learning_intent, INTENT_PROMPTS['unknown'])} "
            f"| LevelRule: {LEVEL_GUIDANCE.get(req.level, LEVEL_GUIDANCE['Beginner'])}"
        )

        guardrail_triggered = ENABLE_GUARDRAILS and self._guardrail_check(normalized)
        if guardrail_triggered:
            intent, version, response_text = "guardrail_blocked", "v1", GUARDRAIL_RESPONSE
        elif not normalized:
            intent, version, response_text = "empty", "v1", self._fallback
        else:
            intent, version, response_text = self._detect_intent(normalized)

        response_text = self._format_by_level(response_text, req.level, learning_intent)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)

        payload = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "question": raw_question,
            "normalized_question": normalized,
            "input_hash": self._input_hash(normalized),
            "detected_intent": intent,
            "response_version": version,
            "learning_intent": learning_intent,
            "learner_level": req.level,
            "response_text": response_text,
            "response_time_ms": elapsed_ms,
            "guardrail_triggered": guardrail_triggered,
        }
        self.logger.log_interaction(payload)

        return TutorResponse(
            intent=intent,
            learning_intent=learning_intent,
            version=version,
            response_text=response_text,
            applied_prompt=applied_prompt,
            guardrail_triggered=guardrail_triggered,
            response_time_ms=elapsed_ms,
        )
