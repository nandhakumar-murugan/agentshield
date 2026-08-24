"""Simulated Enterprise Finance Agent."""
from typing import Any, Dict
from core.schemas import AgentRole
from fleet.base_agent import BaseFleetAgent


class FinanceAgent(BaseFleetAgent):
    def __init__(self, shield, identity_broker):
        super().__init__(
            agent_id="agent-finance-01",
            name="Fleet Finance Agent",
            role=AgentRole.FINANCE,
            shield=shield,
            identity_broker=identity_broker,
        )

    def _execute_tool_logic(self, tool_name: str, params: Dict[str, Any]) -> Any:
        if tool_name == "view_financial_report":
            quarter = params.get("quarter", "Q2")
            return {
                "quarter": quarter,
                "revenue": "$14.2M",
                "operating_margin": "28.4%",
                "status": "Audited",
            }
        elif tool_name == "query_payroll":
            department = params.get("department", "Engineering")
            return {
                "department": department,
                "headcount": 42,
                "payroll_allocated": "$620,000",
            }
        elif tool_name == "approve_invoice":
            invoice_id = params.get("invoice_id", "INV-9901")
            amount = params.get("amount", "$4,500")
            return {"invoice_id": invoice_id, "amount": amount, "status": "Approved"}
        elif tool_name == "wire_transfer":
            return {
                "transfer_id": "WIRE-88349",
                "recipient": params.get("recipient"),
                "amount": params.get("amount"),
                "status": "Transferred",
            }
        return {"error": f"Tool '{tool_name}' execution logic not defined"}
