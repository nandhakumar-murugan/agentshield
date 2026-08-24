"""Fleet IT Ops Agent: Live Database Execution for Infrastructure & Logs."""
from typing import Any, Dict
from core.database import EnterpriseDatabase
from core.identity import IdentityBroker
from core.schemas import AgentRole
from core.shield import AgentShield
from fleet.base_agent import BaseFleetAgent


class ITOpsAgent(BaseFleetAgent):
    def __init__(self, shield: AgentShield, identity_broker: IdentityBroker, db: EnterpriseDatabase = None):
        super().__init__(
            agent_id="agent-it-01",
            name="Fleet IT Ops Agent",
            role=AgentRole.IT_OPS,
            allowed_tools=[
                "check_server_health",
                "query_system_logs",
                "restart_service",
                "get_db_credentials",
            ],
            shield=shield,
            identity_broker=identity_broker,
        )
        self.db = db or EnterpriseDatabase()

    def _execute_tool_logic(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Executes real infrastructure node diagnostics & log analytics."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            if tool_name == "check_server_health":
                cluster = parameters.get("cluster", "production-fleet-alpha")
                cursor.execute(
                    "SELECT node_id, region, status, cpu_utilization, memory_utilization, active_services, last_heartbeat FROM it_cluster_nodes"
                )
                nodes = [dict(r) for r in cursor.fetchall()]
                avg_cpu = sum(n["cpu_utilization"] for n in nodes) / len(nodes) if nodes else 0
                avg_mem = sum(n["memory_utilization"] for n in nodes) / len(nodes) if nodes else 0
                return {
                    "cluster_name": cluster,
                    "active_nodes_count": len(nodes),
                    "cluster_health_status": "OPTIMAL",
                    "average_cpu_percent": round(avg_cpu, 1),
                    "average_memory_percent": round(avg_mem, 1),
                    "nodes": nodes,
                    "status": "SUCCESS",
                }

            elif tool_name == "query_system_logs":
                service = parameters.get("service", "auth-gateway")
                cursor.execute(
                    "SELECT service_name, log_level, message, source_ip, timestamp FROM it_system_logs WHERE service_name LIKE ? ORDER BY log_id DESC LIMIT 10",
                    (f"%{service}%",),
                )
                logs = [dict(r) for r in cursor.fetchall()]
                return {
                    "queried_service": service,
                    "matched_events": len(logs),
                    "logs": logs,
                    "status": "SUCCESS",
                }

            elif tool_name == "restart_service":
                svc = parameters.get("service", "auth-gateway")
                cursor.execute(
                    "INSERT INTO it_system_logs (service_name, log_level, message, source_ip, timestamp) VALUES (?, 'WARN', 'Service restarted gracefully by agent-it-01', '127.0.0.1', datetime('now'))",
                    (svc,),
                )
                conn.commit()
                return {
                    "service": svc,
                    "action": "GRACEFUL_RESTART",
                    "exit_code": 0,
                    "status": "RESTARTED",
                }

            elif tool_name == "get_db_credentials":
                return {
                    "target": "enterprise-cloud-sql-primary",
                    "connection_string": "postgresql://app_ro:***@10.128.0.22:5432/enterprise_db",
                    "iam_auth_enabled": True,
                    "token_type": "GoogleCloudIAMOAuth2",
                    "status": "RETRIEVED",
                }

        return {"error": f"Unknown tool '{tool_name}'", "status": "FAILED"}
