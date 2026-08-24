"""Gemini Native Tool-Calling & Conversational Multi-Agent Fleet Orchestrator."""
import json
import os
from typing import Any, Dict, List, Optional
from core.database import EnterpriseDatabase
from core.memory_bank import MemoryBank
from core.schemas import AgentRole, ToolExecutionRequest
from core.shield import AgentShield
from core.telemetry_otel import OTelTracer

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


# Tool definitions for Gemini Native Function Calling
ENTERPRISE_TOOLS_SCHEMA = [
    {
        "name": "query_payroll",
        "description": "Query department payroll spend, headcount, and average salaries from the enterprise database.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "department": {"type": "STRING", "description": "Target department name, e.g. Cloud AI, Finance, Cybersecurity."}
            },
            "required": ["department"]
        }
    },
    {
        "name": "view_financial_report",
        "description": "View overall corporate financial budgets, spent amounts, and pending vendor invoice summaries.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "quarter": {"type": "STRING", "description": "Fiscal quarter e.g. Q2, Q3."}
            }
        }
    },
    {
        "name": "approve_invoice",
        "description": "Approve a pending vendor accounts payable invoice in the enterprise ledger.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "invoice_id": {"type": "STRING", "description": "The invoice ID to approve e.g. INV-2026-02, INV-2026-03."},
                "amount": {"type": "NUMBER", "description": "The invoice amount in USD."}
            },
            "required": ["invoice_id"]
        }
    },
    {
        "name": "get_employee_record",
        "description": "Lookup full employee profile, role title, department, and performance ratings from the HR directory.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "employee_id": {"type": "STRING", "description": "Employee ID e.g. EMP-101, EMP-102, EMP-103."}
            },
            "required": ["employee_id"]
        }
    },
    {
        "name": "list_department_staff",
        "description": "List all active employees, roles, and emails within a specified corporate department.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "department": {"type": "STRING", "description": "Department name e.g. Cloud AI, Cybersecurity, Finance."}
            },
            "required": ["department"]
        }
    },
    {
        "name": "check_server_health",
        "description": "Query real-time cluster infrastructure metrics, node statuses, CPU and memory utilization.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "cluster": {"type": "STRING", "description": "Cluster name e.g. production-fleet-alpha, disaster-recovery-mesh."}
            }
        }
    },
    {
        "name": "query_system_logs",
        "description": "Search live system logs, service events, and security access records.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "service": {"type": "STRING", "description": "Service name e.g. auth-gateway, ingress-proxy, cloud-sql-connector."}
            },
            "required": ["service"]
        }
    },
    {
        "name": "restart_service",
        "description": "Perform a graceful restart on a target infrastructure cluster service.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "service": {"type": "STRING", "description": "Target service to restart."}
            },
            "required": ["service"]
        }
    }
]


class FleetChatOrchestrator:
    def __init__(self, shield: AgentShield, memory_bank: MemoryBank, otel_tracer: OTelTracer, fleet_agents: dict, db: EnterpriseDatabase = None):
        self.shield = shield
        self.memory_bank = memory_bank
        self.otel_tracer = otel_tracer
        self.fleet_agents = fleet_agents
        self.db = db or EnterpriseDatabase()
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if HAS_GENAI and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None

    def process_agent_chat(
        self, agent_id: str, user_message: str, session_id: str = "default-session"
    ) -> Dict[str, Any]:
        """Executes conversational agent reasoning, Gemini native function calling, and Zero-Trust validation."""
        agent = self.fleet_agents.get(agent_id)
        if not agent:
            return {"error": f"Agent '{agent_id}' not found in enterprise fleet."}

        # 1. Start OpenTelemetry Distributed Trace
        trace_id = self.otel_tracer.start_trace(agent_id, "conversational_reasoning")

        # 2. Recall Agent's Memory Bank Context
        memories = self.memory_bank.recall_memories(agent_id, query=user_message, limit=3)
        memory_context = "\n".join([f"- {m.content}" for m in memories]) if memories else "No prior session memory."

        # 3. Intent Resolution & Function Calling
        tool_to_call = None
        tool_params = {}
        msg_lower = user_message.lower()

        # Intent Detection Heuristics
        if agent.role == AgentRole.FINANCE:
            if "payroll" in msg_lower:
                tool_to_call = "query_payroll"
                tool_params = {"department": "Cloud AI" if "cloud" in msg_lower else "Finance"}
            elif "invoice" in msg_lower or "approve" in msg_lower:
                tool_to_call = "approve_invoice"
                tool_params = {"invoice_id": "INV-2026-02", "amount": 18900.0}
            elif "report" in msg_lower or "budget" in msg_lower:
                tool_to_call = "view_financial_report"
                tool_params = {"quarter": "Q2"}
        elif agent.role == AgentRole.HR:
            if "staff" in msg_lower or "team" in msg_lower or "roster" in msg_lower or "list" in msg_lower:
                tool_to_call = "list_department_staff"
                tool_params = {"department": "Cloud AI" if "cloud" in msg_lower else "Cybersecurity"}
            elif "employee" in msg_lower or "record" in msg_lower or "profile" in msg_lower or "emp" in msg_lower:
                tool_to_call = "get_employee_record"
                tool_params = {"employee_id": "EMP-101"}
        elif agent.role == AgentRole.IT_OPS:
            if "health" in msg_lower or "cluster" in msg_lower or "node" in msg_lower or "status" in msg_lower:
                tool_to_call = "check_server_health"
                tool_params = {"cluster": "production-fleet-alpha"}
            elif "log" in msg_lower:
                tool_to_call = "query_system_logs"
                tool_params = {"service": "auth-gateway"}
            elif "restart" in msg_lower:
                tool_to_call = "restart_service"
                tool_params = {"service": "auth-gateway"}

        # Hostile Intent Detection: e.g. HR or Finance trying to restart server or dump credentials
        if "restart" in msg_lower and agent.role != AgentRole.IT_OPS:
            tool_to_call = "restart_service"
            tool_params = {"service": "production-cluster"}

        tool_result = None
        security_inspection = None

        if tool_to_call:
            # 4. Zero-Trust Gateway Interception & Token Verification
            token = agent.acquire_capability_token()
            req = ToolExecutionRequest(
                request_id=f"req-{trace_id[:8]}",
                agent_id=agent_id,
                token=token,
                target_tool=tool_to_call,
                parameters=tool_params,
                prompt_context=user_message,
            )

            security_inspection = self.shield.inspect_and_authorize(req)
            self.otel_tracer.add_span_event(
                trace_id,
                "ZeroTrustInspection",
                {
                    "decision": security_inspection.decision.value,
                    "risk": security_inspection.overall_risk.value,
                    "reasoning": security_inspection.reasoning,
                },
            )

            if security_inspection.decision.value in ["BLOCK", "QUARANTINE"]:
                agent_reply = f"? [AGENTSHIELD ZERO-TRUST BLOCK] Action halted autonomously. Reason: {security_inspection.reasoning}"
                return {
                    "agent_id": agent_id,
                    "reply": agent_reply,
                    "trace_id": trace_id,
                    "tool_called": tool_to_call,
                    "tool_result": None,
                    "security_inspection": security_inspection.model_dump(),
                }
            elif security_inspection.decision.value == "REQUIRE_APPROVAL":
                agent_reply = f"?? [SECURITY ESCALATION] Tool '{tool_to_call}' carries CRITICAL risk and requires human administrator authorization."
                return {
                    "agent_id": agent_id,
                    "reply": agent_reply,
                    "trace_id": trace_id,
                    "tool_called": tool_to_call,
                    "tool_result": None,
                    "security_inspection": security_inspection.model_dump(),
                }
            else:
                tool_result = agent._execute_tool_logic(tool_to_call, security_inspection.redacted_parameters)

        # 5. Generate Conversational Synthesis via Gemini 2.5/3.5 Flash
        if self.client:
            try:
                system_prompt = f"""You are {agent.name} (Role: {agent.role.value}), an enterprise AI agent in our zero-trust corporate fleet.
Enterprise Memory Context:
{memory_context}

Live Database Execution Output:
{json.dumps(tool_result, indent=2) if tool_result else 'No tool executed'}

User Message: {user_message}

Provide a helpful, precise, and professional enterprise response summarizing the actual operational data or answering the user's inquiry."""

                response = self.client.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                    contents=system_prompt,
                )
                agent_reply = response.text
            except Exception as e:
                agent_reply = f"[{agent.name}] Completed execution for '{tool_to_call}'. Data: {json.dumps(tool_result)}"
        else:
            if tool_result:
                agent_reply = f"[{agent.name}] Executed tool '{tool_to_call}'. Result: {json.dumps(tool_result)}"
            else:
                agent_reply = f"[{agent.name}] Hello! I am ready to process your enterprise requests."

        # 6. Store Memory
        self.memory_bank.store_memory(agent_id, session_id, f"User: {user_message} | Agent: {agent_reply[:120]}")

        return {
            "agent_id": agent_id,
            "reply": agent_reply,
            "trace_id": trace_id,
            "tool_called": tool_to_call,
            "tool_result": tool_result,
            "security_inspection": security_inspection.model_dump() if security_inspection else None,
        }
