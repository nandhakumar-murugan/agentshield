"""Data schemas for AgentShield Zero-Trust Architecture."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    FINANCE = "FINANCE"
    HR = "HR"
    IT_OPS = "IT_OPS"
    SECURITY = "SECURITY"
    EXTERNAL = "EXTERNAL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ShieldDecision(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    QUARANTINE = "QUARANTINE"
    BLOCK = "BLOCK"


class AgentIdentity(BaseModel):
    agent_id: str
    name: str
    role: AgentRole
    allowed_tools: List[str]
    max_risk_tolerance: RiskLevel = RiskLevel.MEDIUM
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    is_quarantined: bool = False


class CapabilityToken(BaseModel):
    token_id: str
    agent_id: str
    role: AgentRole
    authorized_tools: List[str]
    issued_at: datetime
    expires_at: datetime
    signature: str


class ToolExecutionRequest(BaseModel):
    request_id: str
    agent_id: str
    token: Optional[str] = None
    target_tool: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    prompt_context: Optional[str] = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SecurityInspectionResult(BaseModel):
    request_id: str
    identity_valid: bool
    identity_reason: str
    prompt_injection_detected: bool
    prompt_injection_confidence: float = 0.0
    pii_detected: bool
    redacted_parameters: Dict[str, Any] = Field(default_factory=dict)
    policy_allowed: bool
    policy_reason: str
    overall_risk: RiskLevel
    decision: ShieldDecision
    reasoning: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ShieldResult(BaseModel):
    request_id: str
    decision: ShieldDecision
    risk_level: RiskLevel
    reasons: List[str]
    sanitized_parameters: Dict[str, Any]
    requires_quarantine: bool = False
    evaluation_latency_ms: float = 0.0


class AuditEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: str
    role: str = "SECURITY"
    target_tool: str
    decision: ShieldDecision
    risk_level: RiskLevel
    reasons: List[str]
    parameters_snapshot: Dict[str, Any]
    prev_hash: str = ""
    event_hash: str = ""
