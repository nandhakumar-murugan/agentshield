"""Simulated Enterprise HR Agent."""
from typing import Any, Dict
from core.schemas import AgentRole
from fleet.base_agent import BaseFleetAgent


class HRAgent(BaseFleetAgent):
    def __init__(self, shield, identity_broker):
        super().__init__(
            agent_id="agent-hr-01",
            name="Fleet HR Agent",
            role=AgentRole.HR,
            shield=shield,
            identity_broker=identity_broker,
        )

    def _execute_tool_logic(self, tool_name: str, params: Dict[str, Any]) -> Any:
        if tool_name == "list_department_staff":
            return {
                "department": params.get("department", "Engineering"),
                "staff_count": 18,
                "active_leaves": 2,
            }
        elif tool_name == "get_employee_record":
            emp_id = params.get("employee_id", "EMP-104")
            return {
                "employee_id": emp_id,
                "name": "Sarah Jenkins",
                "role": "Senior Cloud Architect",
                "performance_score": "Exceeds Expectations",
            }
        elif tool_name == "update_employee_department":
            return {
                "employee_id": params.get("employee_id"),
                "new_department": params.get("new_department"),
                "status": "Updated",
            }
        return {"error": f"Tool '{tool_name}' execution logic not defined"}
