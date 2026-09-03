"""AuditChain: Cryptographically Linked Immutable Audit Ledger."""
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from core.schemas import AuditEvent, SecurityInspectionResult, ToolExecutionRequest


class AuditChain:
    def __init__(self):
        self.chain: List[AuditEvent] = []
        self._genesis_block()

    def _genesis_block(self):
        genesis = AuditEvent(
            event_id="genesis-event-000",
            timestamp=datetime.now(timezone.utc),
            agent_id="SYSTEM",
            role="SECURITY",
            target_tool="INIT_AGENTSHIELD",
            decision="ALLOW",
            risk_level="LOW",
            reasons=["AgentShield Genesis Node Initialized"],
            parameters_snapshot={},
            prev_hash="0" * 64,
            event_hash="",
        )
        genesis.event_hash = self._compute_hash(genesis)
        self.chain.append(genesis)

    def _compute_hash(self, event: AuditEvent) -> str:
        data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "agent_id": event.agent_id,
            "role": event.role,
            "target_tool": event.target_tool,
            "decision": event.decision.value if hasattr(event.decision, "value") else str(event.decision),
            "risk_level": event.risk_level.value if hasattr(event.risk_level, "value") else str(event.risk_level),
            "reasons": event.reasons,
            "prev_hash": event.prev_hash,
        }
        raw = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def record_event(
        self, request: ToolExecutionRequest, inspection: SecurityInspectionResult
    ) -> AuditEvent:
        prev_hash = self.chain[-1].event_hash if self.chain else "0" * 64

        reasons = [
            f"Identity: {inspection.identity_reason}",
            f"Policy: {inspection.policy_reason}",
        ]
        if inspection.prompt_injection_detected:
            reasons.append(f"Prompt Injection Flagged (conf: {inspection.prompt_injection_confidence:.2f})")
        if inspection.pii_detected:
            reasons.append("DLP: PII parameters redacted")

        event = AuditEvent(
            event_id=f"evt-{len(self.chain):04d}",
            timestamp=datetime.now(timezone.utc),
            agent_id=request.agent_id,
            role=inspection.identity_reason,
            target_tool=request.target_tool,
            decision=inspection.decision,
            risk_level=inspection.overall_risk,
            reasons=reasons,
            parameters_snapshot=inspection.redacted_parameters,
            prev_hash=prev_hash,
            event_hash="",
        )
        event.event_hash = self._compute_hash(event)
        self.chain.append(event)
        return event

    def get_recent_events(self, limit: int = 20) -> List[AuditEvent]:
        return list(reversed(self.chain[-limit:]))

    def verify_chain_integrity(self) -> bool:
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr.prev_hash != prev.event_hash:
                return False
            if curr.event_hash != self._compute_hash(curr):
                return False
        return True
