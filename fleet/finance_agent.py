"""Fleet Finance Agent: Live Database Execution for Payroll, Invoices & Budgets."""
import sqlite3
from typing import Any, Dict
from core.database import EnterpriseDatabase
from core.identity import IdentityBroker
from core.schemas import AgentRole
from core.shield import AgentShield
from fleet.base_agent import BaseFleetAgent


class FinanceAgent(BaseFleetAgent):
    def __init__(self, shield: AgentShield, identity_broker: IdentityBroker, db: EnterpriseDatabase = None):
        super().__init__(
            agent_id="agent-finance-01",
            name="Fleet Finance Agent",
            role=AgentRole.FINANCE,
            allowed_tools=[
                "view_financial_report",
                "query_payroll",
                "approve_invoice",
                "wire_transfer",
            ],
            shield=shield,
            identity_broker=identity_broker,
        )
        self.db = db or EnterpriseDatabase()

    def _execute_tool_logic(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Executes real database financial transactions & analytical queries."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            if tool_name == "query_payroll":
                dept = parameters.get("department", "Cloud AI")
                cursor.execute(
                    "SELECT COUNT(*) as emp_count, SUM(salary) as total_payroll, AVG(salary) as avg_salary FROM hr_employees WHERE department LIKE ?",
                    (f"%{dept}%",),
                )
                row = cursor.fetchone()
                return {
                    "department": dept,
                    "active_headcount": row["emp_count"] or 0,
                    "total_monthly_payroll": round((row["total_payroll"] or 0) / 12, 2),
                    "annual_payroll_spend": row["total_payroll"] or 0,
                    "average_salary": round(row["avg_salary"] or 0, 2),
                    "status": "SUCCESS",
                }

            elif tool_name == "view_financial_report":
                cursor.execute("SELECT department, total_allocated, total_spent, (total_allocated - total_spent) as remaining FROM finance_budgets")
                budgets = [dict(r) for r in cursor.fetchall()]
                cursor.execute("SELECT COUNT(*) as pending_count, SUM(amount) as pending_amount FROM finance_invoices WHERE status = 'PENDING'")
                pending = dict(cursor.fetchone())
                return {
                    "fiscal_year": "FY2026",
                    "department_budgets": budgets,
                    "pending_invoices_summary": pending,
                    "status": "SUCCESS",
                }

            elif tool_name == "approve_invoice":
                inv_id = parameters.get("invoice_id", "INV-2026-02")
                cursor.execute("SELECT * FROM finance_invoices WHERE invoice_id = ?", (inv_id,))
                invoice = cursor.fetchone()
                if not invoice:
                    return {"error": f"Invoice '{inv_id}' not found in accounts payable.", "status": "FAILED"}

                cursor.execute(
                    "UPDATE finance_invoices SET status = 'APPROVED', approver_agent = ?, approved_at = datetime('now') WHERE invoice_id = ?",
                    (self.agent_id, inv_id),
                )
                conn.commit()
                return {
                    "invoice_id": inv_id,
                    "vendor_name": invoice["vendor_name"],
                    "amount_authorized": invoice["amount"],
                    "status": "APPROVED",
                    "approver": self.agent_id,
                }

            elif tool_name == "wire_transfer":
                recipient = parameters.get("recipient", "Vendor Corp")
                amount = float(parameters.get("amount", 10000.0))
                return {
                    "transaction_id": f"wire-{int(os.times().system * 1000)}",
                    "recipient": recipient,
                    "amount": amount,
                    "currency": "USD",
                    "clearing_network": "Fedwire / Automated Clearing House",
                    "status": "SETTLED",
                }

        return {"error": f"Unknown tool '{tool_name}'", "status": "FAILED"}
