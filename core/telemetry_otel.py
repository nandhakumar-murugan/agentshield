"""OpenTelemetry-Compliant Telemetry Exporter & Distributed Tracer."""
import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OpenTelemetrySpan(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    name: str
    kind: str = "INTERNAL"
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    status_code: str = "OK"


class OTelTracer:
    def __init__(self):
        self.spans: List[OpenTelemetrySpan] = []

    def start_trace(self, agent_id: str, tool_name: str) -> str:
        trace_id = f"trace-{uuid.uuid4().hex[:16]}"
        span_id = f"span-{uuid.uuid4().hex[:16]}"
        span = OpenTelemetrySpan(
            trace_id=trace_id,
            span_id=span_id,
            name=f"AgentExecution/{agent_id}/{tool_name}",
            attributes={
                "agent.id": agent_id,
                "agent.tool": tool_name,
                "cloud.provider": "gcp",
                "cloud.platform": "cloud_run",
                "telemetry.sdk.language": "python",
            },
        )
        self.spans.append(span)
        return trace_id

    def add_span_event(self, trace_id: str, name: str, attributes: Dict[str, Any]):
        for span in reversed(self.spans):
            if span.trace_id == trace_id:
                span.events.append(
                    {
                        "name": name,
                        "time": datetime.utcnow().isoformat(),
                        "attributes": attributes,
                    }
                )
                break

    def get_recent_traces(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [s.model_dump() for s in reversed(self.spans[-limit:])]
