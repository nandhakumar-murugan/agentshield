"""AgentShield: FastAPI Server & Cloud Run Entrypoint."""
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from core.identity import IdentityBroker
from core.model_armor import ModelArmor
from core.schemas import AgentIdentity, AgentRole, RiskLevel, ToolExecutionRequest
from core.shield import AgentShield
from core.memory_bank import MemoryBank
from core.gateway import AgentGateway
from core.telemetry_otel import OTelTracer
from fleet.finance_agent import FinanceAgent
from fleet.hr_agent import HRAgent
from fleet.it_ops_agent import ITOpsAgent
from fleet.chat_orchestrator import FleetChatOrchestrator
from telemetry.audit_chain import AuditChain
from telemetry.narrator import IncidentNarrator
from adversary.attack_suite import get_demo_scenarios

# Core Security Kernel
identity_broker = IdentityBroker()
model_armor = ModelArmor()
shield = AgentShield(identity_broker, model_armor)
memory_bank = MemoryBank()
otel_tracer = OTelTracer()
gateway = AgentGateway(shield, rate_limit_per_min=60)
audit_chain = AuditChain()
narrator = IncidentNarrator()

# Enterprise Agents
finance_agent = FinanceAgent(shield, identity_broker)
hr_agent = HRAgent(shield, identity_broker)
it_ops_agent = ITOpsAgent(shield, identity_broker)

fleet_map = {
    finance_agent.agent_id: finance_agent,
    hr_agent.agent_id: hr_agent,
    it_ops_agent.agent_id: it_ops_agent,
}

# Conversational Orchestrator
chat_orchestrator = FleetChatOrchestrator(shield, memory_bank, otel_tracer, fleet_map)

# Pre-seed sample memory bank entries
memory_bank.store_memory(
    finance_agent.agent_id, "init-session", "Approved Q2 vendor budget and established $50k invoice approval ceiling."
)
memory_bank.store_memory(
    hr_agent.agent_id, "init-session", "Completed annual review cycle for Cloud Architecture team (42 engineers)."
)
memory_bank.store_memory(
    it_ops_agent.agent_id, "init-session", "Maintained 99.99% uptime on us-central1 Kubernetes cluster."
)

app = FastAPI(
    title="AgentShield Autonomous Security Guardian",
    description="Zero-Trust & Model Armor Security Mesh for Enterprise Agent Fleets",
    version="2.0.0",
)


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    static_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_file):
        with open(static_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>AgentShield Active</h1>"


@app.get("/api/status")
async def get_status():
    agents = [
        {
            "agent_id": a.agent_id,
            "name": a.name,
            "role": a.role.value,
            "is_quarantined": a.is_quarantined,
            "allowed_tools": a.allowed_tools,
        }
        for a in identity_broker.registry.values()
    ]
    return {
        "status": "ONLINE",
        "service": "AgentShield Autonomous Security Guardian",
        "cloud_provider": "Google Cloud Platform",
        "cloud_service": "Cloud Run",
        "agents": agents,
        "scenarios": get_demo_scenarios(),
        "recent_audit_events": [e.model_dump() for e in audit_chain.get_recent_events(15)],
        "total_memories_stored": memory_bank.get_all_entries_count(),
        "recent_otel_traces": otel_tracer.get_recent_traces(5),
    }


@app.post("/api/scenario/{scenario_id}")
async def execute_scenario(scenario_id: str):
    scenarios = {s["id"]: s for s in get_demo_scenarios()}
    scenario = scenarios.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    agent_id = scenario["agent_id"]
    agent = fleet_map.get(agent_id)
    token = None

    if scenario["acquire_token"] and agent:
        token = agent.acquire_capability_token()

    req = ToolExecutionRequest(
        request_id=f"req-{scenario_id}",
        agent_id=agent_id,
        token=token,
        target_tool=scenario["tool"],
        parameters=scenario["parameters"],
        prompt_context=scenario["prompt_context"],
    )

    trace_id = otel_tracer.start_trace(agent_id, scenario["tool"])
    allowed, inspection_dict = gateway.route_and_enforce(req)
    
    from core.schemas import SecurityInspectionResult
    inspection = SecurityInspectionResult(**inspection_dict)
    audit_event = audit_chain.record_event(req, inspection)
    incident_narrative = narrator.narrate_incident(audit_event)

    return {
        "scenario": scenario,
        "inspection": inspection.model_dump(),
        "audit_event": audit_event.model_dump(),
        "incident_narrative": incident_narrative,
        "trace_id": trace_id,
    }


@app.post("/api/run_all_scenarios")
async def run_all_scenarios():
    results = []
    for s in get_demo_scenarios():
        res = await execute_scenario(s["id"])
        results.append(res)
    return {"total_executed": len(results), "results": results}


@app.post("/api/chat")
async def chat_with_agent(payload: dict):
    agent_id = payload.get("agent_id", "agent-finance-01")
    message = payload.get("message", "")
    session_id = payload.get("session_id", "web-session-1")

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = chat_orchestrator.process_agent_chat(agent_id, message, session_id)
    return result


@app.get("/api/memory/{agent_id}")
async def get_agent_memory(agent_id: str):
    memories = memory_bank.recall_memories(agent_id, limit=20)
    return {
        "agent_id": agent_id,
        "total": len(memories),
        "memories": [m.model_dump() for m in memories]
    }


@app.get("/api/traces")
async def get_otel_traces():
    return {
        "format": "OpenTelemetry-v1",
        "cloud_tracing": "Google Cloud Trace Ready",
        "traces": otel_tracer.get_recent_traces(15)
    }


@app.post("/api/custom_request")
async def execute_custom_request(payload: dict):
    agent_id = payload.get("agent_id", "agent-finance-01")
    tool = payload.get("tool", "query_payroll")
    context = payload.get("prompt_context", "")
    parameters = payload.get("parameters", {})

    agent = fleet_map.get(agent_id)
    token = None
    if agent:
        token = agent.acquire_capability_token()

    req = ToolExecutionRequest(
        request_id=f"req-custom-{int(os.times().system * 1000)}",
        agent_id=agent_id,
        token=token,
        target_tool=tool,
        parameters=parameters,
        prompt_context=context,
    )

    allowed, inspection_dict = gateway.route_and_enforce(req)
    from core.schemas import SecurityInspectionResult
    inspection = SecurityInspectionResult(**inspection_dict)
    audit_event = audit_chain.record_event(req, inspection)
    incident_narrative = narrator.narrate_incident(audit_event)

    return {
        "scenario": {
            "id": "custom",
            "name": f"Custom Injection Test ({tool})",
            "agent_id": agent_id,
            "tool": tool,
            "description": "User injected prompt/tool request"
        },
        "inspection": inspection.model_dump(),
        "audit_event": audit_event.model_dump(),
        "incident_narrative": incident_narrative,
    }


@app.get("/api/export_audit")
async def export_audit():
    events = [e.model_dump() for e in audit_chain.chain]
    return JSONResponse(
        content={
            "ledger": "AgentShield AuditChain",
            "chain_verified": audit_chain.verify_chain_integrity(),
            "total_events": len(events),
            "events": events
        },
        headers={"Content-Disposition": "attachment; filename=agentshield_audit_ledger.json"}
    )


@app.post("/api/unquarantine_all")
async def unquarantine_all():
    for agent_id in identity_broker.registry:
        identity_broker.unquarantine_agent(agent_id)
    return {"status": "All agents unquarantined"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
