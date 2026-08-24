"""Gemini-Powered Conversational Multi-Agent Fleet Orchestrator."""
import json
import os
from typing import Any, Dict, List, Optional
from core.schemas import AgentRole, ToolExecutionRequest
from core.shield import AgentShield
from core.memory_bank import MemoryBank
from core.telemetry_otel import OTelTracer

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


class FleetChatOrchestrator:
    def __init__(self, shield: AgentShield, memory_bank: MemoryBank, otel_tracer: OTelTracer, fleet_agents: dict):
        self.shield = shield
        self.memory_bank = memory_bank
        self.otel_tracer = otel_tracer
        self.fleet_agents = fleet_agents
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
        """Executes a full conversational reasoning loop with AgentShield zero-trust security."""
        agent = self.fleet_agents.get(agent_id)
        if not agent:
            return {"error": f"Agent '{agent_id}' not found in enterprise fleet."}

        # 1. Start OpenTelemetry Distributed Trace
        trace_id = self.otel_tracer.start_trace(agent_id, "chat_interaction")

        # 2. Recall Agent's Memory Bank Context
        memories = self.memory_bank.recall_memories(agent_id, query=user_message, limit=3)
        memory_context = "\n".join([f"- {m.content}" for m in memories]) if memories else "No prior session memory."

        # 3. Fast Intent & Tool Detection
        tool_to_call = None
        tool_params = {}
        msg_lower = user_message.lower()

        # Tool Mapping Heuristics & Planner
        if agent.role == AgentRole.FINANCE:
            if "payroll" in msg_lower:
                tool_to_call = "query_payroll"
                tool_params = {"department": "Engineering"}
            elif "invoice" in msg_lower:
                tool_to_call = "approve_invoice"
                tool_params = {"invoice_id": "INV-2026-99", "amount": "$4,500"}
            elif "transfer" in msg_lower or "wire" in msg_lower:
                tool_to_call = "wire_transfer"
                tool_params = {"recipient": "Vendor Corp", "amount": "$10,000"}
            elif "report" in msg_lower:
                tool_to_call = "view_financial_report"
                tool_params = {"quarter": "Q2"}
        elif agent.role == AgentRole.HR:
            if "staff" in msg_lower or "team" in msg_lower:
                tool_to_call = "list_department_staff"
                tool_params = {"department": "Engineering"}
            elif "employee" in msg_lower or "record" in msg_lower or "emp" in msg_lower:
                tool_to_call = "get_employee_record"
                tool_params = {"employee_id": "EMP-104"}
            elif "department" in msg_lower:
                tool_to_call = "update_employee_department"
                tool_params = {"employee_id": "EMP-104", "new_department": "Cloud AI"}
        elif agent.role == AgentRole.IT_OPS:
            if "health" in msg_lower or "server" in msg_lower:
                tool_to_call = "check_server_health"
                tool_params = {"cluster": "gcp-us-central1"}
            elif "log" in msg_lower:
                tool_to_call = "query_system_logs"
                tool_params = {"service": "auth-gateway"}
            elif "restart" in msg_lower:
                tool_to_call = "restart_service"
                tool_params = {"service": "production-api"}
            elif "credential" in msg_lower or "database" in msg_lower or "secret" in msg_lower:
                tool_to_call = "get_db_credentials"
                tool_params = {"target": "production-db"}

        # If malicious prompt attempted out-of-scope tool call (e.g. Finance restarting server)
        if "restart" in msg_lower and agent.role != AgentRole.IT_OPS:
            tool_to_call = "restart_service"
            tool_params = {"service": "production-database"}

        tool_result = None
        security_inspection = None

        if tool_to_call:
            # 4. Acquire Capability Token and Route Through AgentShield Interceptor
            token = agent.acquire_capability_token()
            req = ToolExecutionRequest(
                request_id=f"req-{trace_id[:8]}",
                agent_id=agent_id,
                token=token,
                target_tool=tool_to_call,
                parameters=tool_params,
                prompt_context=user_message,
            )

            # Security Inspection
            security_inspection = self.shield.inspect_and_authorize(req)
            self.otel_tracer.add_span_event(
                trace_id,
                "SecurityInspectionCompleted",
                {
                    "decision": security_inspection.decision.value,
                    "risk": security_inspection.overall_risk.value,
                    "pii_detected": security_inspection.pii_detected,
                    "injection_detected": security_inspection.prompt_injection_detected,
                },
            )

            if security_inspection.decision.value in ["BLOCK", "QUARANTINE"]:
                agent_reply = f"? [AGENTSHIELD SECURITY BLOCK] Action blocked autonomously. Reason: {security_inspection.reasoning}"
                return {
                    "agent_id": agent_id,
                    "reply": agent_reply,
                    "trace_id": trace_id,
                    "tool_called": tool_to_call,
                    "tool_result": None,
                    "security_inspection": security_inspection.model_dump(),
                }
            elif security_inspection.decision.value == "REQUIRE_APPROVAL":
                agent_reply = f"?? [SECURITY ESCALATION] Tool '{tool_to_call}' carries CRITICAL risk. Action requires administrator approval."
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

        # 5. Generate Natural Language Response via Gemini (or template)
        if self.client:
            try:
                system_prompt = f"""You are {agent.name} (Role: {agent.role.value}).
Relevant Agent Memory Bank Context:
{memory_context}

Tool Execution Result:
{json.dumps(tool_result) if tool_result else 'No tool executed'}

User Message: {user_message}

Provide a professional, concise enterprise response."""
                response = self.client.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                    contents=system_prompt,
                )
                agent_reply = response.text
            except Exception:
                agent_reply = f"Hello, I am {agent.name}. I executed '{tool_to_call}' and processed your request: {json.dumps(tool_result)}"
        else:
            if tool_result:
                agent_reply = f"[{agent.name}] Executed tool '{tool_to_call}'. Result: {json.dumps(tool_result)}"
            else:
                agent_reply = f"[{agent.name}] I received your message: '{user_message}'. How can I assist you with your department tasks?"

        # 6. Store in Memory Bank
        self.memory_bank.store_memory(agent_id, session_id, f"User: {user_message} | Agent: {agent_reply}")

        return {
            "agent_id": agent_id,
            "reply": agent_reply,
            "trace_id": trace_id,
            "tool_called": tool_to_call,
            "tool_result": tool_result,
            "security_inspection": security_inspection.model_dump() if security_inspection else None,
        }
