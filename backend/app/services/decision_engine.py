from app.models.enums import FallbackMode, ProviderName, RiskFlag, RouteTarget
from app.models.route import ClassificationResult, RouteDecision, RouteRequest


class DecisionEngine:
    """Converts classifier scores into explainable provider routing decisions."""

    def decide(self, request: RouteRequest, classification: ClassificationResult) -> RouteDecision:
        if request.force_route:
            return self._forced_decision(request.force_route)

        flags = set(classification.risk_flags)
        privacy = classification.privacy_score
        complexity = classification.complexity_score
        latency = classification.latency_score
        cost = classification.cost_score

        reason_codes: list[str] = []

        if privacy >= 0.85 or RiskFlag.SECRET in flags:
            reason_codes.extend(["privacy.local_first", "sensitive_content.detected"])
            if complexity >= 0.76:
                reason_codes.append("complexity.hybrid_candidate_but_privacy_blocks_cloud")
            return RouteDecision(
                target=RouteTarget.LOCAL,
                primary_provider=ProviderName.OLLAMA,
                backup_providers=[ProviderName.MOCK_CLOUD],
                confidence=0.91,
                fallback_mode=FallbackMode.LOCAL_TO_CLOUD,
                reason_codes=reason_codes,
                decision_summary="Sensitive content detected, so RouteIQ selected local-first inference with controlled fallback.",
            )

        if privacy >= 0.62 and complexity >= 0.70:
            reason_codes.extend(["privacy.moderate_high", "complexity.high", "hybrid.best_fit"])
            return RouteDecision(
                target=RouteTarget.HYBRID,
                primary_provider=ProviderName.OLLAMA,
                backup_providers=[ProviderName.FIREWORKS, ProviderName.MOCK_CLOUD],
                confidence=0.86,
                fallback_mode=FallbackMode.HYBRID_TO_LOCAL,
                reason_codes=reason_codes,
                decision_summary="Task is complex but privacy-sensitive, so RouteIQ selected hybrid execution.",
            )

        if complexity >= 0.72 and privacy < 0.62 and latency < 0.78:
            reason_codes.extend(["complexity.high", "privacy.cloud_allowed"])
            return RouteDecision(
                target=RouteTarget.CLOUD,
                primary_provider=ProviderName.FIREWORKS,
                backup_providers=[ProviderName.MOCK_CLOUD, ProviderName.OLLAMA],
                confidence=0.88,
                fallback_mode=FallbackMode.CLOUD_TO_MOCK,
                reason_codes=reason_codes,
                decision_summary="Task complexity justifies cloud inference while privacy risk remains acceptable.",
            )

        if cost >= 0.72:
            reason_codes.append("cost.local_saves_tokens")
        if latency >= 0.70:
            reason_codes.append("latency.local_preferred")
        if complexity < 0.72:
            reason_codes.append("complexity.local_capable")

        return RouteDecision(
            target=RouteTarget.LOCAL,
            primary_provider=ProviderName.OLLAMA,
            backup_providers=[ProviderName.FIREWORKS, ProviderName.MOCK_CLOUD],
            confidence=0.82,
            fallback_mode=FallbackMode.LOCAL_TO_CLOUD,
            reason_codes=reason_codes or ["default.local_first"],
            decision_summary="Task appears suitable for local inference, reducing cloud token usage.",
        )

    @staticmethod
    def _forced_decision(target: RouteTarget) -> RouteDecision:
        provider = {
            RouteTarget.LOCAL: ProviderName.OLLAMA,
            RouteTarget.CLOUD: ProviderName.FIREWORKS,
            RouteTarget.HYBRID: ProviderName.OLLAMA,
        }[target]
        return RouteDecision(
            target=target,
            primary_provider=provider,
            backup_providers=[ProviderName.MOCK_CLOUD],
            confidence=1.0,
            fallback_mode=FallbackMode.NONE,
            reason_codes=["force_route.user_override"],
            decision_summary=f"Route was manually forced to {target.value} by request override.",
        )
