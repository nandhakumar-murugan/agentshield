"""Agent Gateway: Unified Ingress, Rate Limiting & Zero-Trust Routing."""
import time
from typing import Dict, Tuple
from core.schemas import RiskLevel, ShieldDecision, ToolExecutionRequest
from core.shield import AgentShield


class AgentGateway:
    def __init__(self, shield: AgentShield, rate_limit_per_min: int = 60):
        self.shield = shield
        self.rate_limit = rate_limit_per_min
        self.request_timestamps: Dict[str, list] = {}

    def _check_rate_limit(self, agent_id: str) -> bool:
        now = time.time()
        if agent_id not in self.request_timestamps:
            self.request_timestamps[agent_id] = []

        # Prune timestamps older than 60s
        self.request_timestamps[agent_id] = [
            ts for ts in self.request_timestamps[agent_id] if now - ts < 60
        ]

        if len(self.request_timestamps[agent_id]) >= self.rate_limit:
            return False

        self.request_timestamps[agent_id].append(now)
        return True

    def route_and_enforce(self, request: ToolExecutionRequest) -> Tuple[bool, dict]:
        """Ingress enforcement point for all agentic tool execution requests."""
        # 1. Rate Limiting / DoS Prevention
        if not self._check_rate_limit(request.agent_id):
            return False, {
                "decision": ShieldDecision.BLOCK.value,
                "risk": RiskLevel.HIGH.value,
                "reason": f"Rate limit exceeded for agent '{request.agent_id}' (> {self.rate_limit} req/min)",
                "status": "RATE_LIMITED",
            }

        # 2. Deep Security Inspection via Shield
        inspection = self.shield.inspect_and_authorize(request)

        return inspection.policy_allowed, inspection.model_dump()
