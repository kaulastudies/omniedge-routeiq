import re

from app.models.enums import PrivacyLevel, RiskFlag
from app.models.route import ClassificationResult, RouteRequest
from app.utils.tokens import estimate_tokens


PII_PATTERNS = [
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){10,14}\b"),
    re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"),  # Aadhaar-like
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE),  # PAN-like
]

SECRET_PATTERNS = [
    re.compile(r"(?:api[_-]?key|secret|token|password|private[_-]?key)\s*[:=]", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PRIVATE )?KEY-----"),
]

COMPLEXITY_TERMS = {
    "architecture",
    "multi-agent",
    "reason",
    "debug",
    "optimize",
    "refactor",
    "legal",
    "medical",
    "financial",
    "compare",
    "research",
    "proof",
    "algorithm",
    "production",
    "security",
}

CODE_TERMS = {"def ", "class ", "import ", "const ", "function", "SELECT ", "npm ", "docker", "fastapi", "next.js"}


class RoutingClassifier:
    """Scores incoming tasks across privacy, complexity, latency pressure, and cost sensitivity."""

    def classify(self, request: RouteRequest) -> ClassificationResult:
        prompt = request.prompt
        lower = prompt.lower()
        estimated_tokens = estimate_tokens(prompt)
        flags: set[RiskFlag] = set()
        explanation: list[str] = []

        if request.privacy_level in {PrivacyLevel.CONFIDENTIAL, PrivacyLevel.REGULATED}:
            flags.add(RiskFlag.PII)
            explanation.append(f"Declared privacy level is {request.privacy_level.value}.")

        if any(pattern.search(prompt) for pattern in PII_PATTERNS):
            flags.add(RiskFlag.PII)
            explanation.append("Prompt contains likely personal identifiers.")

        if any(pattern.search(prompt) for pattern in SECRET_PATTERNS):
            flags.add(RiskFlag.SECRET)
            explanation.append("Prompt appears to contain secrets or credentials.")

        if any(term in lower for term in ["insurance", "invoice", "bank", "payment", "salary", "tax"]):
            flags.add(RiskFlag.FINANCIAL)
            explanation.append("Prompt includes financial or payment context.")

        if any(term in lower for term in ["patient", "diagnosis", "medical", "health", "hospital"]):
            flags.add(RiskFlag.HEALTH)
            explanation.append("Prompt includes healthcare context.")

        if any(term in prompt for term in CODE_TERMS):
            flags.add(RiskFlag.SOURCE_CODE)
            explanation.append("Prompt includes code or developer instructions.")

        if estimated_tokens > 2_500:
            flags.add(RiskFlag.LONG_CONTEXT)
            explanation.append("Prompt is long enough to affect latency and cost.")

        complexity_hits = sum(1 for term in COMPLEXITY_TERMS if term in lower)
        complexity_score = min(1.0, 0.18 + (estimated_tokens / 6_000) + (complexity_hits * 0.07))

        if complexity_score >= 0.68:
            flags.add(RiskFlag.COMPLEX_REASONING)
            explanation.append("Task likely needs stronger reasoning or larger context handling.")

        latency_score = 0.3
        if request.max_latency_ms is not None:
            latency_score = max(0.0, min(1.0, 1 - (request.max_latency_ms / 12_000)))
            if request.max_latency_ms <= 2_500:
                flags.add(RiskFlag.URGENT_LATENCY)
                explanation.append("Request has a strict latency target.")

        cost_score = 0.3
        if request.token_budget_usd is not None:
            projected_cloud_cost = (estimated_tokens / 1_000) * 0.0009
            cost_score = max(0.0, min(1.0, 1 - (request.token_budget_usd / max(projected_cloud_cost, 0.000001))))
            if request.token_budget_usd <= projected_cloud_cost:
                flags.add(RiskFlag.COST_SENSITIVE)
                explanation.append("Cloud token budget is tight for estimated prompt size.")

        privacy_score = self._privacy_score(request.privacy_level, flags)

        if not explanation:
            explanation.append("No strong privacy or complexity risks detected.")

        return ClassificationResult(
            privacy_score=round(privacy_score, 3),
            complexity_score=round(complexity_score, 3),
            latency_score=round(latency_score, 3),
            cost_score=round(cost_score, 3),
            estimated_input_tokens=estimated_tokens,
            risk_flags=sorted(flags, key=lambda item: item.value),
            explanation=explanation,
        )

    @staticmethod
    def _privacy_score(privacy_level: PrivacyLevel, flags: set[RiskFlag]) -> float:
        declared = {
            PrivacyLevel.PUBLIC: 0.1,
            PrivacyLevel.INTERNAL: 0.35,
            PrivacyLevel.CONFIDENTIAL: 0.72,
            PrivacyLevel.REGULATED: 0.92,
        }[privacy_level]
        flag_boost = 0.0
        if RiskFlag.PII in flags:
            flag_boost += 0.22
        if RiskFlag.SECRET in flags:
            flag_boost += 0.35
        if RiskFlag.HEALTH in flags or RiskFlag.FINANCIAL in flags:
            flag_boost += 0.13
        return min(1.0, declared + flag_boost)
