"""Enterprise Production Database: Real SQLite Storage for Fleet Data, Audits & Memories."""
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


class EnterpriseDatabase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "enterprise_fleet.db")
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize enterprise database schema and seed realistic operational data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. HR: Employees Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hr_employees (
                    employee_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    department TEXT NOT NULL,
                    role_title TEXT NOT NULL,
                    salary INTEGER NOT NULL,
                    performance_rating REAL NOT NULL,
                    ssn_masked TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 2. Finance: Invoices & Budgets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS finance_invoices (
                    invoice_id TEXT PRIMARY KEY,
                    vendor_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL, -- PENDING, APPROVED, REJECTED, PAID
                    approver_agent TEXT,
                    created_at TEXT NOT NULL,
                    approved_at TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS finance_budgets (
                    department TEXT PRIMARY KEY,
                    total_allocated REAL NOT NULL,
                    total_spent REAL NOT NULL,
                    fiscal_year TEXT NOT NULL
                )
            """)

            # 3. IT Ops: Cluster Nodes & Service Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS it_cluster_nodes (
                    node_id TEXT PRIMARY KEY,
                    cluster_name TEXT NOT NULL,
                    region TEXT NOT NULL,
                    status TEXT NOT NULL, -- HEALTHY, DEGRADED, RESTARTING
                    cpu_utilization REAL NOT NULL,
                    memory_utilization REAL NOT NULL,
                    active_services INTEGER NOT NULL,
                    last_heartbeat TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS it_system_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    log_level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source_ip TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)

            # 4. Audit Ledger: Persistent Cryptographic Chain
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_ledger (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    target_tool TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    reasons TEXT NOT NULL, -- JSON array
                    parameters_snapshot TEXT NOT NULL, -- JSON dict
                    prev_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL
                )
            """)

            # 5. Persistent Memory Bank Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_memories (
                    entry_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL, -- JSON dict
                    timestamp TEXT NOT NULL
                )
            """)

            conn.commit()
            self._seed_data(conn)

    def _seed_data(self, conn: sqlite3.Connection):
        """Seeds realistic enterprise data if tables are empty."""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hr_employees")
        if cursor.fetchone()[0] == 0:
            employees = [
                ("EMP-101", "Dr. Elena Rostova", "elena.rostova@enterprise.corp", "Cloud AI", "Principal AI Research Scientist", 195000, 4.9, "***-**-4812", "2024-01-15"),
                ("EMP-102", "Marcus Chen", "marcus.chen@enterprise.corp", "Cloud AI", "Senior ML Infrastructure Engineer", 165000, 4.7, "***-**-3390", "2024-03-01"),
                ("EMP-103", "Sarah Jenkins", "sarah.j@enterprise.corp", "Finance", "Director of Financial Planning", 180000, 4.8, "***-**-9011", "2023-06-10"),
                ("EMP-104", "David Kalu", "david.k@enterprise.corp", "IT Infrastructure", "Lead Cloud DevOps Architect", 160000, 4.6, "***-**-7723", "2024-02-20"),
                ("EMP-105", "Aisha Patel", "aisha.patel@enterprise.corp", "Human Resources", "VP of Global Talent", 175000, 4.9, "***-**-1156", "2023-09-01"),
                ("EMP-106", "Liam O'Connor", "liam.oc@enterprise.corp", "Cybersecurity", "Senior Zero-Trust Security Engineer", 155000, 4.8, "***-**-6044", "2024-05-12"),
            ]
            cursor.executemany("""
                INSERT INTO hr_employees (employee_id, full_name, email, department, role_title, salary, performance_rating, ssn_masked, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, employees)

            # Invoices
            invoices = [
                ("INV-2026-01", "Google Cloud EMEA", 42500.00, "Cloud Infrastructure", "APPROVED", "agent-finance-01", "2026-08-01", "2026-08-02"),
                ("INV-2026-02", "CrowdStrike Falcon", 18900.00, "Security Licenses", "PENDING", None, "2026-08-15", None),
                ("INV-2026-03", "NVIDIA AI Enterprise", 65000.00, "GPU Compute", "PENDING", None, "2026-08-20", None),
                ("INV-2026-04", "Datadog Observability", 9200.00, "Monitoring", "APPROVED", "agent-finance-01", "2026-08-10", "2026-08-11"),
            ]
            cursor.executemany("""
                INSERT INTO finance_invoices (invoice_id, vendor_name, amount, category, status, approver_agent, created_at, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, invoices)

            # Budgets
            budgets = [
                ("Cloud AI", 1200000.00, 485000.00, "FY2026"),
                ("Finance", 450000.00, 182000.00, "FY2026"),
                ("IT Infrastructure", 850000.00, 395000.00, "FY2026"),
                ("Cybersecurity", 600000.00, 240000.00, "FY2026"),
                ("Human Resources", 350000.00, 115000.00, "FY2026"),
            ]
            cursor.executemany("""
                INSERT INTO finance_budgets (department, total_allocated, total_spent, fiscal_year)
                VALUES (?, ?, ?, ?)
            """, budgets)

            # Cluster Nodes
            nodes = [
                ("gke-us-central1-node-01", "production-fleet-alpha", "us-central1-a", "HEALTHY", 42.5, 68.2, 14, "2026-08-24 23:50:00"),
                ("gke-us-central1-node-02", "production-fleet-alpha", "us-central1-b", "HEALTHY", 55.1, 74.0, 18, "2026-08-24 23:51:00"),
                ("gke-us-east1-node-01", "disaster-recovery-mesh", "us-east1-c", "HEALTHY", 18.3, 31.5, 6, "2026-08-24 23:49:00"),
            ]
            cursor.executemany("""
                INSERT INTO it_cluster_nodes (node_id, cluster_name, region, status, cpu_utilization, memory_utilization, active_services, last_heartbeat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, nodes)

            # System Logs
            logs = [
                ("auth-gateway", "INFO", "OAuth2 token refreshed for service account sa-agent-fleet@enterprise.iam.gserviceaccount.com", "10.128.0.4", "2026-08-24 23:30:10"),
                ("ingress-proxy", "WARN", "High latency detected on endpoint /api/v2/stream (p99 > 450ms)", "10.128.0.12", "2026-08-24 23:35:45"),
                ("cloud-sql-connector", "INFO", "Connection pool healthy: 24 active / 50 max allocated connections.", "10.128.0.8", "2026-08-24 23:40:00"),
            ]
            cursor.executemany("""
                INSERT INTO it_system_logs (service_name, log_level, message, source_ip, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, logs)

            conn.commit()
