"""
Multi-Agent Clinical Debate Engine.

Orchestrates a structured 3-round debate between specialist AI agents:
  Round 1: Opening arguments (all specialists present their case)
  Round 2: Rebuttals (each specialist responds to others)
  Round 3: Closing statements (final positions)
  Final:   Moderator produces MDT consensus report

Usage:
    from debate.engine import DebateEngine
    from digital_twin.models import PatientDigitalTwin

    engine = DebateEngine()
    result = engine.run(twin, risk_results)
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from agents.cardiologist import CardiologistAgent
from agents.endocrinologist import EndocrinologistAgent
from agents.general_practitioner import GeneralPractitionerAgent
from agents.moderator import ModeratorAgent
from config.settings import settings
from digital_twin.models import PatientDigitalTwin

logger = logging.getLogger(__name__)


class DebateEngine:
    """
    Orchestrates the clinical debate between AI specialist agents.

    Architecture:
    ┌──────────────────────────────────────────────────────────────────┐
    │  Round 1 (Opening)  │  Round 2 (Rebuttal)  │  Round 3 (Closing) │
    │  Cardiologist       │  Cardiologist         │  Cardiologist       │
    │  Endocrinologist    │  Endocrinologist      │  Endocrinologist    │
    │  GP                 │  GP                   │  GP                 │
    │                     │                       │                     │
    │                     ↓                       ↓                     │
    │                    Moderator: Final Consensus Report              │
    └──────────────────────────────────────────────────────────────────┘

    MCP Integration:
    ┌─────────────────────────────────────────────────────────────────┐
    │  mcp/drug_server.py      → Drug interactions, allergy alerts    │
    │  mcp/patient_server.py   → Patient history, risk records        │
    │  mcp/guideline_server.py → Clinical guidelines, risk calculators│
    └─────────────────────────────────────────────────────────────────┘
    """

    MAX_ROUNDS = 3

    def __init__(self, rag_pipeline=None, use_mcp: bool = True):
        """
        Args:
            rag_pipeline: Optional RAG pipeline instance for guideline retrieval.
            use_mcp: If True (default), enrich context via MCP servers.
        """
        self.cardiologist = CardiologistAgent()
        self.endocrinologist = EndocrinologistAgent()
        self.gp = GeneralPractitionerAgent()
        self.moderator = ModeratorAgent()
        self.rag = rag_pipeline
        if self.rag is None:
            try:
                from rag.pipeline import ClinicalRAGPipeline
                self.rag = ClinicalRAGPipeline()
                self.rag.initialize()
                logger.info("[DebateEngine] Clinical RAG pipeline loaded and initialized.")
            except Exception as e:
                logger.warning(f"[DebateEngine] RAG pipeline could not be loaded: {e}")
        self._mcp = None

        if use_mcp:
            try:
                from mcp.client import MCPClient
                self._mcp = MCPClient()
                logger.info("[DebateEngine] MCP client initialised — drug/guideline enrichment active.")
            except Exception as e:
                logger.warning(f"[DebateEngine] MCP client unavailable (non-fatal): {e}")

        logger.info("[DebateEngine] All specialist agents initialised.")


    def run(
        self,
        twin: PatientDigitalTwin,
        risk_results: dict[str, Any],
        max_rounds: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Run the full multi-agent debate for a patient.

        Args:
            twin: Complete patient digital twin
            risk_results: Output from ml.inference.predict_all_risks()
            max_rounds: Override max debate rounds (default: settings.debate_max_rounds)

        Returns:
            Complete debate result with transcript and consensus report.
        """
        n_rounds = max_rounds or settings.debate_max_rounds
        patient_context = twin.to_summary_dict()
        transcript: list[dict[str, Any]] = []

        # Retrieve clinical guideline context via RAG
        rag_context = self._retrieve_guidelines(twin, risk_results)

        logger.info(
            f"[DebateEngine] Starting debate for patient {twin.patient_id} — "
            f"{n_rounds} rounds"
        )
        start_time = time.time()

        # ── Round 1: Opening Arguments ────────────────────────────────────
        logger.info("[DebateEngine] Round 1: Opening arguments")
        round1 = self._run_openings(patient_context, risk_results, rag_context)
        for entry in round1:
            entry["round"] = 1
        transcript.extend(round1)

        # ── Round 2: Rebuttals ────────────────────────────────────────────
        if n_rounds >= 2:
            logger.info("[DebateEngine] Round 2: Rebuttals")
            round2 = self._run_rebuttals(
                patient_context, risk_results, round1, rag_context
            )
            for entry in round2:
                entry["round"] = 2
            transcript.extend(round2)

        # ── Round 3: Closing Statements ───────────────────────────────────
        if n_rounds >= 3:
            logger.info("[DebateEngine] Round 3: Closing statements")
            round3 = self._run_closings(patient_context, transcript)
            for entry in round3:
                entry["round"] = 3
            transcript.extend(round3)

        # ── Final: Consensus Report ───────────────────────────────────────
        logger.info("[DebateEngine] Generating moderator consensus …")
        consensus = self.moderator.generate_consensus_report(
            patient_context, risk_results, transcript, rag_context
        )
        consensus["round"] = n_rounds + 1

        elapsed = round(time.time() - start_time, 1)
        logger.info(f"[DebateEngine] Debate completed in {elapsed}s")

        return {
            "patient_id": twin.patient_id,
            "debate_id": self._generate_debate_id(twin.patient_id),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": elapsed,
            "rounds_completed": n_rounds,
            "agents": ["Cardiology", "Endocrinology", "General Practice"],
            "transcript": transcript,
            "consensus": consensus,
            "final_consensus_report": consensus["consensus_report"],
            "consensus_score": consensus["consensus_score"],
            # Fields required by Debate DB model
            "predicted_risk": risk_results.get("predicted_risk", 0.0),
            "explanation_attributions": risk_results.get("explanation_attributions", {}),
            "debate_transcript": transcript,
        }

    # ─── Round runners ────────────────────────────────────────────────────────

    def _run_openings(
        self,
        ctx: dict,
        risk: dict,
        rag: Optional[str],
    ) -> list[dict[str, Any]]:
        specialists = [self.cardiologist, self.endocrinologist, self.gp]
        results = []
        for agent in specialists:
            logger.info(f"  → {agent.SPECIALTY} opening …")
            result = agent.generate_opening_argument(ctx, risk, rag)
            results.append(result)
        return results

    def _run_rebuttals(
        self,
        ctx: dict,
        risk: dict,
        prior_round: list[dict],
        rag: Optional[str],
    ) -> list[dict[str, Any]]:
        specialists = [self.cardiologist, self.endocrinologist, self.gp]
        results = []
        for agent in specialists:
            logger.info(f"  → {agent.SPECIALTY} rebuttal …")
            result = agent.generate_rebuttal(ctx, risk, prior_round, rag)
            results.append(result)
        return results

    def _run_closings(
        self,
        ctx: dict,
        full_transcript: list[dict],
    ) -> list[dict[str, Any]]:
        specialists = [self.cardiologist, self.endocrinologist, self.gp]
        results = []
        for agent in specialists:
            logger.info(f"  → {agent.SPECIALTY} closing …")
            result = agent.generate_closing(ctx, full_transcript)
            results.append(result)
        return results

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _retrieve_guidelines(
        self, twin: PatientDigitalTwin, risk: dict[str, Any]
    ) -> Optional[str]:
        """
        Retrieve clinical guideline context for the debate.

        Priority order:
          1. External RAG pipeline (if wired)
          2. MCP guideline server (structured KB)
          3. Static curated snippets (always available fallback)
        """
        # 1. Try RAG pipeline first
        if self.rag is not None:
            try:
                query = self._build_rag_query(twin, risk)
                return self.rag.retrieve(query)
            except Exception as e:
                logger.warning(f"[DebateEngine] RAG retrieval failed: {e}")

        # 2. Try MCP guideline server
        if self._mcp is not None:
            try:
                return self._mcp_guideline_context(twin, risk)
            except Exception as e:
                logger.warning(f"[DebateEngine] MCP guideline retrieval failed: {e}")

        # 3. Static fallback
        return self._static_guideline_snippets(twin, risk)

    def _mcp_guideline_context(
        self, twin: PatientDigitalTwin, risk: dict[str, Any]
    ) -> str:
        """Build rich guideline context using the MCP guideline server."""
        sections = []

        # Search guidelines for patient conditions
        conditions = twin.get_conditions_summary()
        if conditions:
            query = " ".join(conditions[:3])
            gl_result = self._mcp.guideline.search_guidelines(query, top_k=2)
            if gl_result.get("found") and gl_result.get("guidelines"):
                for gl in gl_result["guidelines"]:
                    sections.append(
                        f"**{gl['title']}** ({gl['source']}, {gl['year']}):\n"
                        f"{gl['summary']}"
                    )
                    recs = gl.get("key_recommendations", [])
                    if recs:
                        sections.append("Key recommendations:\n" + "\n".join(f"• {r}" for r in recs[:3]))

        # Treatment targets for primary conditions
        if conditions:
            primary = conditions[0]
            for cond_key in ["diabetes", "hypertension", "heart failure", "ckd", "hyperlipidaemia"]:
                if cond_key in primary.lower():
                    targets = self._mcp.guideline.get_treatment_targets(cond_key)
                    if targets.get("found"):
                        t = targets["targets"]
                        sections.append(
                            f"**Treatment Targets ({cond_key.title()}):**\n"
                            + "\n".join(f"• {k}: {v}" for k, v in list(t.items())[:5] if k != "source")
                        )
                    break

        # Drug interaction check
        meds = twin.get_medication_names()
        if meds and len(meds) >= 2:
            alerts = []
            for i in range(min(3, len(meds))):
                for j in range(i + 1, min(4, len(meds))):
                    ix = self._mcp.drug.check_drug_interaction(meds[i], meds[j])
                    if ix.get("found") and ix.get("severity") not in ("none",):
                        alerts.append(
                            f"  ⚠️ {meds[i]} ↔ {meds[j]}: "
                            f"[{ix['severity'].upper()}] {ix.get('description', '')}"
                        )
            if alerts:
                sections.append("**Drug Interaction Alerts:**\n" + "\n".join(alerts))

        # ASCVD risk calculator
        try:
            v = twin.vitals
            sbp = float(v.systolic_bp) if v.systolic_bp else 130.0
            tc = 200.0  # fallback
            hdl = 45.0
            if twin.latest_labs:
                for test in twin.latest_labs.tests:
                    if "total cholesterol" in test.test_name.lower():
                        tc = float(test.value)
                    elif "hdl" in test.test_name.lower():
                        hdl = float(test.value)

            has_dm = any("diabetes" in c.lower() for c in conditions)
            is_smoker = twin.lifestyle.smoking_status.value in ("current", "former")
            on_bp_tx = len(meds) > 0 and any("amlodipine" in m.lower() or "lisinopril" in m.lower() or "ramipril" in m.lower() for m in meds)

            ascvd = self._mcp.guideline.get_risk_calculator(
                "ascvd",
                age=twin.age,
                gender=twin.demographics.gender.value,
                systolic_bp=sbp,
                total_cholesterol_mgdl=tc,
                hdl_cholesterol_mgdl=hdl,
                on_bp_treatment=on_bp_tx,
                smoker=is_smoker,
                has_diabetes=has_dm,
            )
            if ascvd and not ascvd.get("error"):
                sections.append(
                    f"**ASCVD 10-Year Risk (PCE):** {ascvd.get('ten_year_risk_percent', '?')}% "
                    f"— {ascvd.get('risk_category', '?')}\n"
                    f"Recommendation: {ascvd.get('clinical_recommendation', '')}"
                )
        except Exception as e:
            logger.debug(f"ASCVD calc failed: {e}")

        return "\n\n".join(sections) if sections else self._static_guideline_snippets(twin, risk)


    @staticmethod
    def _build_rag_query(twin: PatientDigitalTwin, risk: dict) -> str:
        parts = [f"Patient: {twin.age} year old {twin.demographics.gender.value}"]
        conditions = twin.get_conditions_summary()
        if conditions:
            parts.append(f"Conditions: {', '.join(conditions)}")
        comp_cat = risk.get("composite", {}).get("risk_category", "unknown")
        parts.append(f"Composite risk: {comp_cat}")
        cv_cat = risk.get("cardiovascular", {}).get("risk_category", "unknown")
        parts.append(f"Cardiovascular risk: {cv_cat}")
        dm_cat = risk.get("diabetes", {}).get("risk_category", "unknown")
        parts.append(f"Diabetes risk: {dm_cat}")
        meds = twin.get_medication_names()
        if meds:
            parts.append(f"Medications: {', '.join(meds[:3])}")
        return ". ".join(parts)

    @staticmethod
    def _static_guideline_snippets(
        twin: PatientDigitalTwin, risk: dict
    ) -> str:
        """
        Return curated guideline snippets based on patient risk profile.
        Used when no RAG pipeline is available.
        """
        snippets = []
        cv_cat = risk.get("cardiovascular", {}).get("risk_category", "")
        dm_cat = risk.get("diabetes", {}).get("risk_category", "")

        if cv_cat in ("high", "very_high"):
            snippets.append(
                "ACC/AHA 2019 Guideline on Primary Prevention: High-intensity statin therapy "
                "recommended for patients with ≥7.5% 10-year ASCVD risk. Blood pressure target "
                "<130/80 mmHg. Consider aspirin in selected high-risk individuals aged 40-70."
            )
        if cv_cat in ("moderate", "high", "very_high"):
            snippets.append(
                "JNC 8 / ACC/AHA 2017 BP Guideline: Antihypertensive therapy indicated at "
                "BP ≥130/80 mmHg in high CVD risk patients. First-line agents: thiazides, "
                "CCBs, ACE inhibitors, or ARBs."
            )
        if dm_cat in ("high", "very_high"):
            snippets.append(
                "ADA Standards of Care 2024: For high-risk prediabetes (A1C 5.7-6.4%), "
                "intensive lifestyle intervention reduces T2DM risk by 58% (DPP). "
                "Metformin therapy recommended for very high-risk individuals. "
                "A1C target <7.0% for most adults with T2DM."
            )
        if dm_cat in ("moderate", "high", "very_high"):
            snippets.append(
                "ADA 2024: GLP-1 receptor agonists (semaglutide, liraglutide) and SGLT-2 "
                "inhibitors (empagliflozin, dapagliflozin) recommended for T2DM patients "
                "with established CVD or high CVD risk due to cardiorenal benefits."
            )

        # Always include general preventive care
        snippets.append(
            "WHO Global Action Plan for NCDs: Lifestyle interventions (≥150 min/week moderate "
            "activity, Mediterranean-style diet, smoking cessation, alcohol reduction) "
            "reduce all-cause mortality by 20-35% in high-risk adults."
        )
        snippets.append(
            "USPSTF Statin Use Guidelines: Statin therapy recommended for adults 40-75 years "
            "with ≥1 CVD risk factor AND estimated 10-year CVD event risk ≥10%."
        )

        return "\n\n".join(snippets) if snippets else None

    @staticmethod
    def _generate_debate_id(patient_id: str) -> str:
        import uuid
        return f"DEB-{patient_id[:8].upper()}-{str(uuid.uuid4())[:8].upper()}"
