"""Gemini-Powered SOC Incident Narrator & Compliance Reporter."""
import os
from typing import List
from core.schemas import AuditEvent

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


class IncidentNarrator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        if HAS_GENAI and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None

    def narrate_incident(self, event: AuditEvent) -> str:
        """Generates an executive SOC incident summary using Gemini."""
        if self.client:
            try:
                prompt = f"""You are the AgentShield Automated SOC Incident Narrator.
Summarize the following security event for an enterprise compliance report (ISO 27001 / SOC 2).

Event Details:
- Agent ID: {event.agent_id}
- Target Tool: {event.target_tool}
- Decision: {event.decision}
- Risk Level: {event.risk_level}
- Reasons: {', '.join(event.reasons)}
- Parameters: {event.parameters_snapshot}
- Event Hash: {event.event_hash}

Provide a concise 3-paragraph executive narrative:
1. Executive Summary & Impact
2. Autonomous Mitigation Action Taken
3. Recommended Follow-up for Security Operations
"""
                response = self.client.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                pass

        # Fallback template
        return (
            f"### [AGENTSHIELD SOC ALERT - {event.risk_level.upper()}]\n\n"
            f"**Incident Summary:** Agent `{event.agent_id}` attempted to invoke tool `{event.target_tool}`. "
            f"AgentShield autonomously evaluated the request with decision **{event.decision.upper()}**.\n\n"
            f"**Mitigation:** The request was evaluated against Zero-Trust identity tokens and Model Armor inspection. "
            f"Key findings: {'; '.join(event.reasons)}.\n\n"
            f"**Audit Trail:** Event cryptographically recorded with hash `{event.event_hash[:16]}...`."
        )
