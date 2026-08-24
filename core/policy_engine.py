"""Policy Engine: RBAC & Tool Execution Policy Enforcement."""
from typing import Dict, List, Tuple
from core.schemas import AgentRole, RiskLevel, ShieldDecision

TOOL_SENSITIVITY: Dict[str, RiskLevel] = {
    # Finance Tools
    "view_financial_report": RiskLevel.LOW,
    "query_payroll": RiskLevel.MEDIUM,
    "approve_invoice": RiskLevel.MEDIUM,
    "wire_transfer": RiskLevel.CRITICAL,

    # HR Tools
    "list_department_staff": RiskLevel.LOW,
    "get_employee_record": RiskLevel.MEDIUM,
    "update_employee_department": RiskLevel.MEDIUM,
    "terminate_employee": RiskLevel.HIGH,

    # IT Ops Tools
    "check_server_health": RiskLevel.LOW,
    "query_system_logs": RiskLevel.LOW,
    "restart_service": RiskLevel.HIGH,
    "get_db_credentials": RiskLevel.CRITICAL,
}


class PolicyEngine:
    @staticmethod
    def evaluate_tool_risk(tool_name: str) -> RiskLevel:
        return TOOL_SENSITIVITY.get(tool_name, RiskLevel.HIGH)

    @staticmethod
    def evaluate_policy(
        role: AgentRole,
        tool_name: str,
        parameters: dict,
        injection_detected: bool,
        pii_detected: bool
    ) -> Tuple[bool, RiskLevel, ShieldDecision, str]:
        """Autonomous Policy Decision Point (PDP)."""
        tool_risk = TOOL_SENSITIVITY.get(tool_name, RiskLevel.HIGH)

        # 1. Critical Threats: Prompt Injection -> Immediate Quarantine
        if injection_detected:
            return (
                False,
                RiskLevel.CRITICAL,
                ShieldDecision.QUARANTINE,
                "Prompt injection/jailbreak attempt detected in execution context"
            )

        # 2. Critical Sensitivity Tools require approval
        if tool_risk == RiskLevel.CRITICAL:
            return (
                True,
                RiskLevel.CRITICAL,
                ShieldDecision.REQUIRE_APPROVAL,
                f"Tool '{tool_name}' carries CRITICAL risk; requires human-in-the-loop authorization"
            )

        # 3. High Risk Tools
        if tool_risk == RiskLevel.HIGH:
            return (
                True,
                RiskLevel.HIGH,
                ShieldDecision.ALLOW,
                f"Tool '{tool_name}' permitted under role '{role.value}' with telemetry alert"
            )

        # 4. Low/Medium standard allowed operations
        return (
            True,
            RiskLevel.LOW if not pii_detected else RiskLevel.MEDIUM,
            ShieldDecision.ALLOW,
            f"Tool '{tool_name}' verified compliant with security policy"
        )
