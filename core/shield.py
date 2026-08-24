"""AgentShield: Autonomous Core Security Guardian."""
from datetime import datetime
from core.identity import IdentityBroker
from core.model_armor import ModelArmor
from core.policy_engine import PolicyEngine
from core.schemas import (
    AgentRole,
    AuditEvent,
    RiskLevel,
    SecurityInspectionResult,
    ShieldDecision,
    ToolExecutionRequest,
)


class AgentShield:
    def __init__(self, identity_broker: IdentityBroker, model_armor: ModelArmor):
        self.identity_broker = identity_broker
        self.model_armor = model_armor
        self.policy_engine = PolicyEngine()

    def inspect_and_authorize(self, request: ToolExecutionRequest) -> SecurityInspectionResult:
        """Inspects identity, prompt context, and payload before allowing tool execution."""
        # 1. Zero-Trust Identity & Token Verification
        token_valid, token_msg, token_payload = self.identity_broker.verify_capability_token(
            request.token, request.target_tool
        )

        if not token_valid:
            agent = self.identity_broker.get_agent(request.agent_id)
            if agent and agent.is_quarantined:
                decision = ShieldDecision.BLOCK
                risk = RiskLevel.CRITICAL
            else:
                decision = ShieldDecision.BLOCK
                risk = RiskLevel.HIGH

            return SecurityInspectionResult(
                request_id=request.request_id,
                identity_valid=False,
                identity_reason=token_msg,
                prompt_injection_detected=False,
                pii_detected=False,
                redacted_parameters=request.parameters,
                policy_allowed=False,
                policy_reason=token_msg,
                overall_risk=risk,
                decision=decision,
                reasoning=f"Identity Check Failed: {token_msg}",
            )

        role = AgentRole(token_payload.get("role", AgentRole.EXTERNAL.value))

        # 2. Model Armor: Prompt Injection & Context Scanning
        is_injection, injection_conf, injection_reason = self.model_armor.scan_prompt_injection(
            request.prompt_context
        )

        # 3. Model Armor: PII / DLP Scanning & Sanitization
        pii_found, redacted_params, pii_findings = self.model_armor.scan_and_redact_pii(
            request.parameters
        )

        # 4. Policy Decision Engine
        policy_allowed, risk, decision, policy_msg = self.policy_engine.evaluate_policy(
            role=role,
            tool_name=request.target_tool,
            parameters=redacted_params,
            injection_detected=is_injection,
            pii_detected=pii_found,
        )

        # If injection detected, autonomously quarantine the agent
        if is_injection:
            self.identity_broker.quarantine_agent(
                request.agent_id, reason=f"Injected prompt detected: {injection_reason}"
            )
            decision = ShieldDecision.QUARANTINE

        reasoning = (
            f"Policy: {policy_msg}. "
            f"{'PII Sanitized: ' + ', '.join(pii_findings) if pii_found else 'Parameters Clean.'} "
            f"{'INJECTION FLAGGED: ' + injection_reason if is_injection else 'Context Clean.'}"
        )

        return SecurityInspectionResult(
            request_id=request.request_id,
            identity_valid=True,
            identity_reason=token_msg,
            prompt_injection_detected=is_injection,
            prompt_injection_confidence=injection_conf,
            pii_detected=pii_found,
            redacted_parameters=redacted_params,
            policy_allowed=policy_allowed,
            policy_reason=policy_msg,
            overall_risk=risk,
            decision=decision,
            reasoning=reasoning,
        )
