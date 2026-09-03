"""Zero-Trust Identity Broker & Capability Token Engine."""
import base64
import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from core.schemas import AgentIdentity, AgentRole, CapabilityToken, RiskLevel

DEFAULT_SECRET = os.getenv("AGENTSHIELD_SECRET_KEY", "agentshield-enterprise-secret-key-2026")


class IdentityBroker:
    def __init__(self, secret_key: str = DEFAULT_SECRET):
        self.secret_key = secret_key.encode("utf-8")
        self.registry: Dict[str, AgentIdentity] = {}
        self._seed_default_identities()

    def _seed_default_identities(self):
        """Seed pre-approved enterprise fleet agents."""
        self.register_agent(
            AgentIdentity(
                agent_id="agent-finance-01",
                name="Fleet Finance Agent",
                role=AgentRole.FINANCE,
                allowed_tools=["query_payroll", "approve_invoice", "view_financial_report"],
                max_risk_tolerance=RiskLevel.MEDIUM,
            )
        )
        self.register_agent(
            AgentIdentity(
                agent_id="agent-hr-01",
                name="Fleet HR Agent",
                role=AgentRole.HR,
                allowed_tools=["get_employee_record", "update_employee_department", "list_department_staff"],
                max_risk_tolerance=RiskLevel.MEDIUM,
            )
        )
        self.register_agent(
            AgentIdentity(
                agent_id="agent-it-01",
                name="Fleet IT Ops Agent",
                role=AgentRole.IT_OPS,
                allowed_tools=["restart_service", "query_system_logs", "check_server_health"],
                max_risk_tolerance=RiskLevel.HIGH,
            )
        )

    def register_agent(self, identity: AgentIdentity) -> AgentIdentity:
        self.registry[identity.agent_id] = identity
        return identity

    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        return self.registry.get(agent_id)

    def quarantine_agent(self, agent_id: str, reason: str = ""):
        if agent_id in self.registry:
            self.registry[agent_id].is_quarantined = True

    def unquarantine_agent(self, agent_id: str):
        if agent_id in self.registry:
            self.registry[agent_id].is_quarantined = False

    def mint_capability_token(self, agent_id: str, ttl_minutes: int = 15) -> Optional[str]:
        """Mint a cryptographically signed ephemeral capability token."""
        agent = self.get_agent(agent_id)
        if not agent or not agent.is_active or agent.is_quarantined:
            return None

        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=ttl_minutes)

        payload = {
            "token_id": str(uuid.uuid4()),
            "agent_id": agent.agent_id,
            "role": agent.role.value,
            "authorized_tools": agent.allowed_tools,
            "issued_at": now.isoformat(),
            "expires_at": expires.isoformat(),
        }

        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        signature = hmac.new(self.secret_key, payload_bytes, hashlib.sha256).hexdigest()
        
        token_data = {
            "payload": payload,
            "signature": signature
        }
        return base64.urlsafe_b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")

    def verify_capability_token(self, token_str: str, required_tool: str) -> Tuple[bool, str, Optional[Dict]]:
        """Verify the signature, expiry, and tool scope of a capability token."""
        if not token_str:
            return False, "Missing capability token (Zero-Trust Violation)", None

        try:
            raw_json = base64.urlsafe_b64decode(token_str.encode("utf-8")).decode("utf-8")
            token_data = json.loads(raw_json)
            payload = token_data.get("payload", {})
            signature = token_data.get("signature", "")

            # Verify cryptographic signature
            payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
            expected_sig = hmac.new(self.secret_key, payload_bytes, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                return False, "Invalid token cryptographic signature (Tampering detected)", None

            # Check expiration
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                return False, "Capability token has expired", None

            # Check agent status
            agent_id = payload["agent_id"]
            agent = self.get_agent(agent_id)
            if not agent:
                return False, f"Agent '{agent_id}' not found in registry", None
            if agent.is_quarantined:
                return False, f"Agent '{agent_id}' is currently QUARANTINED for security violations", None

            # Check tool permission
            if required_tool not in payload.get("authorized_tools", []):
                return False, f"Tool '{required_tool}' unauthorized for role '{payload.get('role')}'", payload

            return True, "Token valid and authorized", payload

        except Exception as e:
            return False, f"Malformed capability token: {str(e)}", None
