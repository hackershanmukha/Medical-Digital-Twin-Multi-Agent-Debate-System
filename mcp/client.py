"""
MCP Client — Connects the debate agents to all 3 MCP servers.

Usage (from an agent or the debate engine):

    from mcp.client import MCPClient

    client = MCPClient()

    # Drug server
    info = client.drug.get_drug_info("metformin")
    ix   = client.drug.check_drug_interaction("metformin", "empagliflozin")

    # Patient server
    summary = client.patient.get_patient_summary("patient-uuid")

    # Guideline server
    guidelines = client.guideline.search_guidelines("diabetes hypertension treatment")
    ascvd      = client.guideline.get_risk_calculator("ascvd", age=62, gender="male", ...)
"""
from __future__ import annotations

import json
import subprocess
import sys
import os
from typing import Any, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_DIR = os.path.join(ROOT, "mcp")


class _StdioMCPProxy:
    """
    Lightweight stdio-based MCP client proxy.
    Launches the server as a subprocess, sends JSON-RPC calls, returns results.

    For hackathon/demo use. In production use the official MCP Python SDK client.
    """

    def __init__(self, server_script: str):
        self._server_script = server_script
        self._tools: dict[str, callable] = {}
        self._build_tool_stubs()

    def _call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Invoke a tool on the MCP server via stdio JSON-RPC.
        Spawns a subprocess for each call (simple but correct for demo).
        """
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": kwargs,
            },
        }
        try:
            proc = subprocess.run(
                [sys.executable, self._server_script],
                input=json.dumps(request) + "\n",
                capture_output=True,
                text=True,
                timeout=30,
            )
            stdout = proc.stdout.strip()
            if not stdout:
                return {"error": f"No response from {self._server_script}"}

            # Find last JSON line
            for line in reversed(stdout.splitlines()):
                line = line.strip()
                if line.startswith("{"):
                    parsed = json.loads(line)
                    result = parsed.get("result", {})
                    # MCP wraps text results in content array
                    if isinstance(result, dict) and "content" in result:
                        content = result["content"]
                        if isinstance(content, list) and content:
                            text = content[0].get("text", "")
                            return json.loads(text) if text.startswith("{") or text.startswith("[") else text
                    return result
        except subprocess.TimeoutExpired:
            return {"error": f"MCP server timeout calling {tool_name}"}
        except Exception as e:
            return {"error": str(e)}
        return {"error": "No valid JSON-RPC response found"}

    def _build_tool_stubs(self):
        """Introspect available tools via JSON-RPC initialize/tools/list."""
        pass  # We define methods directly on each proxy class

    def __getattr__(self, name: str):
        """Dynamically create tool call stubs."""
        def tool_caller(**kwargs):
            return self._call_tool(name, **kwargs)
        return tool_caller


class _DrugProxy(_StdioMCPProxy):
    def __init__(self):
        super().__init__(os.path.join(MCP_DIR, "drug_server.py"))

    def get_drug_info(self, drug_name: str) -> dict:
        return self._call_tool("get_drug_info", drug_name=drug_name)

    def check_drug_interaction(self, drug_a: str, drug_b: str) -> dict:
        return self._call_tool("check_drug_interaction", drug_a=drug_a, drug_b=drug_b)

    def check_allergy_alert(self, drug_name: str, patient_allergies: list[str]) -> dict:
        return self._call_tool("check_allergy_alert", drug_name=drug_name, patient_allergies=patient_allergies)

    def get_contraindications(
        self, drug_name: str, egfr: float = 90.0,
        has_liver_disease: bool = False, is_pregnant: bool = False,
        comorbidities: Optional[list[str]] = None,
    ) -> dict:
        return self._call_tool(
            "get_contraindications",
            drug_name=drug_name, egfr=egfr,
            has_liver_disease=has_liver_disease, is_pregnant=is_pregnant,
            comorbidities=comorbidities or [],
        )

    def get_dosage_guidance(
        self, drug_name: str, indication: str,
        egfr: float = 90.0, has_liver_disease: bool = False, age: int = 50,
    ) -> dict:
        return self._call_tool(
            "get_dosage_guidance",
            drug_name=drug_name, indication=indication,
            egfr=egfr, has_liver_disease=has_liver_disease, age=age,
        )


class _PatientProxy(_StdioMCPProxy):
    def __init__(self):
        super().__init__(os.path.join(MCP_DIR, "patient_server.py"))

    def get_patient_summary(self, patient_id: str) -> dict:
        return self._call_tool("get_patient_summary", patient_id=patient_id)

    def get_patient_risk_history(self, patient_id: str, limit: int = 5) -> dict:
        return self._call_tool("get_patient_risk_history", patient_id=patient_id, limit=limit)

    def get_abnormal_labs(self, patient_id: str, critical_only: bool = False) -> dict:
        return self._call_tool("get_abnormal_labs", patient_id=patient_id, critical_only=critical_only)

    def get_medication_list(self, patient_id: str, active_only: bool = True) -> dict:
        return self._call_tool("get_medication_list", patient_id=patient_id, active_only=active_only)

    def get_comorbidity_burden(self, patient_id: str) -> dict:
        return self._call_tool("get_comorbidity_burden", patient_id=patient_id)

    def get_vitals_trend(self, patient_id: str, limit: int = 10) -> dict:
        return self._call_tool("get_vitals_trend", patient_id=patient_id, limit=limit)


class _GuidelineProxy(_StdioMCPProxy):
    def __init__(self):
        super().__init__(os.path.join(MCP_DIR, "guideline_server.py"))

    def search_guidelines(self, query: str, top_k: int = 3) -> dict:
        return self._call_tool("search_guidelines", query=query, top_k=top_k)

    def get_risk_calculator(self, calculator: str, age: int, gender: str, **kwargs) -> dict:
        return self._call_tool("get_risk_calculator", calculator=calculator, age=age, gender=gender, **kwargs)

    def get_treatment_targets(self, condition: str) -> dict:
        return self._call_tool("get_treatment_targets", condition=condition)

    def get_screening_schedule(self, condition: str) -> dict:
        return self._call_tool("get_screening_schedule", condition=condition)

    def get_clinical_evidence(self, drug_or_intervention: str) -> dict:
        return self._call_tool("get_clinical_evidence", drug_or_intervention=drug_or_intervention)


class MCPClient:
    """
    Unified MCP client providing access to all 3 clinical services.

    Example:
        client = MCPClient()
        info = client.drug.get_drug_info("metformin")
        gl   = client.guideline.search_guidelines("T2DM + CVD treatment")
        pt   = client.patient.get_patient_summary("uuid-here")
    """

    def __init__(self):
        self.drug = _DrugProxy()
        self.patient = _PatientProxy()
        self.guideline = _GuidelineProxy()

    def build_agent_context(
        self,
        patient_id: Optional[str] = None,
        medications: Optional[list[str]] = None,
        conditions: Optional[list[str]] = None,
        allergies: Optional[list[str]] = None,
        egfr: float = 90.0,
    ) -> str:
        """
        Build a rich textual context block for injection into agent prompts.
        Aggregates patient data, drug checks, and guideline snippets.

        Args:
            patient_id: Optional DB patient UUID (fetches live data).
            medications: Current medications (if no patient_id).
            conditions: Active conditions (if no patient_id).
            allergies: Allergy list (if no patient_id).
            egfr: eGFR for drug safety checks.

        Returns:
            Formatted multi-section context string.
        """
        sections = []

        # Patient summary from DB
        if patient_id:
            pt = self.patient.get_patient_summary(patient_id)
            if pt.get("found"):
                conditions = pt.get("active_conditions", conditions or [])
                medications = pt.get("active_medications", medications or [])
                allergies = pt.get("allergies", allergies or [])
                sections.append(f"**Patient Record:**\n{json.dumps(pt, indent=2)[:800]}")

        # Drug interaction checks
        if medications and len(medications) >= 2:
            meds_clean = [m.split()[0] for m in medications]  # extract name
            interaction_alerts = []
            for i in range(len(meds_clean)):
                for j in range(i + 1, len(meds_clean)):
                    ix = self.drug.check_drug_interaction(meds_clean[i], meds_clean[j])
                    if ix.get("found") and ix.get("severity") not in ("none", "unknown"):
                        interaction_alerts.append(
                            f"  ⚠️ {meds_clean[i]} ↔ {meds_clean[j]}: "
                            f"{ix.get('severity', '?').upper()} — {ix.get('description', '')}"
                        )
            if interaction_alerts:
                sections.append("**Drug Interactions:**\n" + "\n".join(interaction_alerts))

        # Guideline retrieval
        if conditions:
            query = " ".join(conditions[:3])
            gl = self.guideline.search_guidelines(query, top_k=2)
            if gl.get("found") and gl.get("guidelines"):
                gl_txt = []
                for g in gl["guidelines"][:2]:
                    gl_txt.append(f"- **{g['title']}** ({g['source']}, {g['year']}):\n  {g['summary'][:300]}")
                sections.append("**Relevant Guidelines:**\n" + "\n".join(gl_txt))

        return "\n\n".join(sections) if sections else "No MCP context available."
