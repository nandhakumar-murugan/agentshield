"""Base Enterprise Fleet Agent."""
import uuid
from typing import Any, Dict, Optional
from core.schemas import AgentRole, ToolExecutionRequest


class BaseFleetAgent:
    def __init__(self, agent_id: str, name: str, role: AgentRole, shield, identity_broker, allowed_tools: list = None):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.shield = shield
        self.identity_broker = identity_broker
        self.allowed_tools = allowed_tools or []
        self.active_token: Optional[str] = None

    def acquire_capability_token(self) -> Optional[str]:
        """Requests a JIT capability token from the Identity Broker."""
        self.active_token = self.identity_broker.mint_capability_token(self.agent_id)
        return self.active_token

    def invoke_tool(
        self, tool_name: str, parameters: Dict[str, Any], prompt_context: str = ""
    ) -> Dict[str, Any]:
        """Invokes a tool protected by the AgentShield security interceptor."""
        request = ToolExecutionRequest(
            request_id=f"req-{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            token=self.active_token,
            target_tool=tool_name,
            parameters=parameters,
            prompt_context=prompt_context,
        )

        inspection = self.shield.inspect_and_authorize(request)

        if inspection.decision.value in ["BLOCK", "QUARANTINE"]:
            return {
                "status": "BLOCKED",
                "decision": inspection.decision.value,
                "risk": inspection.overall_risk.value,
                "reason": inspection.reasoning,
                "result": None,
            }

        if inspection.decision.value == "REQUIRE_APPROVAL":
            return {
                "status": "PENDING_APPROVAL",
                "decision": inspection.decision.value,
                "risk": inspection.overall_risk.value,
                "reason": inspection.reasoning,
                "result": None,
            }

        # Execute Tool Logic
        execution_result = self._execute_tool_logic(tool_name, inspection.redacted_parameters)
        return {
            "status": "SUCCESS",
            "decision": inspection.decision.value,
            "risk": inspection.overall_risk.value,
            "reason": inspection.reasoning,
            "result": execution_result,
        }

    def _execute_tool_logic(self, tool_name: str, params: Dict[str, Any]) -> Any:
        raise NotImplementedError("Subclasses must implement specific tool execution.")
