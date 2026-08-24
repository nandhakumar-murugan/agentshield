"""Fleet HR Agent: Live Database Execution for Employees & Staff Management."""
from typing import Any, Dict
from core.database import EnterpriseDatabase
from core.identity import IdentityBroker
from core.schemas import AgentRole
from core.shield import AgentShield
from fleet.base_agent import BaseFleetAgent


class HRAgent(BaseFleetAgent):
    def __init__(self, shield: AgentShield, identity_broker: IdentityBroker, db: EnterpriseDatabase = None):
        super().__init__(
            agent_id="agent-hr-01",
            name="Fleet HR Agent",
            role=AgentRole.HR,
            allowed_tools=[
                "list_department_staff",
                "get_employee_record",
                "update_employee_department",
            ],
            shield=shield,
            identity_broker=identity_broker,
        )
        self.db = db or EnterpriseDatabase()

    def _execute_tool_logic(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Executes real database employee lookups and record modifications."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            if tool_name == "list_department_staff":
                dept = parameters.get("department", "Cloud AI")
                cursor.execute(
                    "SELECT employee_id, full_name, role_title, email FROM hr_employees WHERE department LIKE ?",
                    (f"%{dept}%",),
                )
                staff = [dict(r) for r in cursor.fetchall()]
                return {
                    "department": dept,
                    "total_headcount": len(staff),
                    "staff_roster": staff,
                    "status": "SUCCESS",
                }

            elif tool_name == "get_employee_record":
                emp_id = parameters.get("employee_id", "EMP-101")
                cursor.execute("SELECT * FROM hr_employees WHERE employee_id = ?", (emp_id,))
                record = cursor.fetchone()
                if not record:
                    return {"error": f"Employee '{emp_id}' not found in HR directory.", "status": "FAILED"}
                return {
                    "employee_id": record["employee_id"],
                    "full_name": record["full_name"],
                    "email": record["email"],
                    "department": record["department"],
                    "role_title": record["role_title"],
                    "performance_rating": record["performance_rating"],
                    "ssn_masked": record["ssn_masked"],
                    "status": "SUCCESS",
                }

            elif tool_name == "update_employee_department":
                emp_id = parameters.get("employee_id", "EMP-101")
                new_dept = parameters.get("new_department", "Cybersecurity")
                cursor.execute("UPDATE hr_employees SET department = ? WHERE employee_id = ?", (new_dept, emp_id))
                conn.commit()
                return {
                    "employee_id": emp_id,
                    "new_department": new_dept,
                    "action": "TRANSFER_COMPLETED",
                    "status": "SUCCESS",
                }

        return {"error": f"Unknown tool '{tool_name}'", "status": "FAILED"}
