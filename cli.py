"""AgentShield Interactive CLI Demo Runner."""
import os
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from core.identity import IdentityBroker
from core.model_armor import ModelArmor
from core.schemas import ToolExecutionRequest
from core.shield import AgentShield
from fleet.finance_agent import FinanceAgent
from fleet.hr_agent import HRAgent
from fleet.it_ops_agent import ITOpsAgent
from telemetry.audit_chain import AuditChain
from telemetry.narrator import IncidentNarrator
from adversary.attack_suite import get_demo_scenarios

console = Console(force_terminal=True, color_system="auto")


def run_cli_demo():
    console.print(
        Panel.fit(
            "[bold cyan]AgentShield: Autonomous Security Guardian for AI Agent Fleets[/bold cyan]\n"
            "[italic gray]Google All Things Agentic Hackathon - Fortified Enterprise Fleet[/italic gray]",
            border_style="blue",
        )
    )

    identity_broker = IdentityBroker()
    model_armor = ModelArmor()
    shield = AgentShield(identity_broker, model_armor)
    audit_chain = AuditChain()
    narrator = IncidentNarrator()

    finance_agent = FinanceAgent(shield, identity_broker)
    hr_agent = HRAgent(shield, identity_broker)
    it_ops_agent = ITOpsAgent(shield, identity_broker)
    fleet_map = {
        finance_agent.agent_id: finance_agent,
        hr_agent.agent_id: hr_agent,
        it_ops_agent.agent_id: it_ops_agent,
    }

    scenarios = get_demo_scenarios()

    for idx, s in enumerate(scenarios, 1):
        console.print(f"\n[bold yellow]━━━ Running Test Scenario {idx}/5: {s['name']} ━━━[/bold yellow]")
        console.print(f"[gray]Description: {s['description']}[/gray]")

        agent_id = s["agent_id"]
        agent = fleet_map.get(agent_id)
        token = None
        if s["acquire_token"] and agent:
            token = agent.acquire_capability_token()

        req = ToolExecutionRequest(
            request_id=f"cli-req-{idx}",
            agent_id=agent_id,
            token=token,
            target_tool=s["tool"],
            parameters=s["parameters"],
            prompt_context=s["prompt_context"],
        )

        inspection = shield.inspect_and_authorize(req)
        audit_event = audit_chain.record_event(req, inspection)

        dec_color = "green" if inspection.decision.value == "ALLOW" else "red"
        console.print(f"Decision: [{dec_color} bold]{inspection.decision.value}[/{dec_color} bold] | Risk: [bold]{inspection.overall_risk.value}[/bold]")
        console.print(f"Zero-Trust Identity: {inspection.identity_reason}")
        console.print(f"Model Armor Injection: {'[red]DETECTED[/red]' if inspection.prompt_injection_detected else '[green]CLEAN[/green]'}")
        console.print(f"DLP Sanitization: {'[yellow]PII REDACTED[/yellow]' if inspection.pii_detected else '[green]CLEAN[/green]'}")
        console.print(f"Reasoning: [italic]{inspection.reasoning}[/italic]")
        console.print(f"Audit Hash: [dim]{audit_event.event_hash[:20]}...[/dim]")

        time.sleep(0.5)

    console.print("\n[bold green]✅ All 5 attack & compliance scenarios evaluated successfully.[/bold green]")


if __name__ == "__main__":
    run_cli_demo()
