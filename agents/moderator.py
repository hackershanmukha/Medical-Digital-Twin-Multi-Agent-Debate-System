"""
Moderator Agent — Consensus builder and final report generator.

The moderator does not argue a position. Instead, it:
1. Facilitates the debate structure
2. Identifies consensus and remaining disagreements
3. Synthesises a final clinical consensus report
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from google.genai import types

from agents.base_agent import ClinicalAgent, _get_client, _ensure_configured
from config.settings import settings

logger = logging.getLogger(__name__)


class ModeratorAgent(ClinicalAgent):
    SPECIALTY = "Moderator"
    EMOJI = "⚖️"
    PERSONA = """You are Dr. Sarah Chen, a clinical informaticist and chief medical officer
who moderates multi-disciplinary team (MDT) discussions.

Your role is NOT to advocate for a specialty position, but to:
- Synthesise diverse specialist viewpoints fairly and objectively
- Identify where specialists agree and where they diverge
- Weigh evidence quality and clinical urgency
- Produce clear, actionable, prioritised recommendations
- Flag uncertainties and areas requiring further data
- Ensure the final plan is comprehensive, safe, and implementable

You have expertise in clinical decision-making, evidence synthesis, and MDT facilitation.
You draw from all specialties impartially and produce a consensus that reflects
the weight of evidence from the entire debate."""

    def generate_consensus_report(
        self,
        patient_context: dict[str, Any],
        risk_results: dict[str, Any],
        full_transcript: list[dict[str, Any]],
        rag_context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Generate the final MDT consensus report after all debate rounds.
        """
        _ensure_configured()
        patient_txt = self._build_patient_summary(patient_context, risk_results)
        debate_txt = self._format_transcript(full_transcript)
        guideline_txt = f"\n\n**Evidence Base:**\n{rag_context}" if rag_context else ""

        prompt = (
            "You are the moderator of a multi-disciplinary clinical AI debate.\n\n"
            f"=== PATIENT ===\n{patient_txt}{guideline_txt}\n\n"
            f"=== FULL DEBATE TRANSCRIPT ===\n{debate_txt}\n\n"
            "=== YOUR TASK ===\n"
            "Synthesise a formal MDT Consensus Report with the following sections:\n\n"
            "**1. CLINICAL SUMMARY**\n"
            "Brief summary of the patient's risk profile.\n\n"
            "**2. CONSENSUS FINDINGS**\n"
            "Key points ALL specialists agreed on.\n\n"
            "**3. AREAS OF DISAGREEMENT**\n"
            "Where specialists diverged and why — with your assessment of which view is better supported.\n\n"
            "**4. PRIORITISED RECOMMENDATIONS**\n"
            "Numbered list of actionable recommendations, ordered by clinical urgency.\n"
            "For each: [intervention] — [rationale] — [target] — [timeframe]\n\n"
            "**5. MONITORING PLAN**\n"
            "What to monitor, how frequently, and alert thresholds.\n\n"
            "**6. UNCERTAINTY & GAPS**\n"
            "What additional data would improve confidence.\n\n"
            "**7. OVERALL RISK VERDICT**\n"
            "Single-sentence plain-language verdict for the clinical record.\n\n"
            f"Format the report clearly. Be specific and cite evidence from the debate."
        )

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.PERSONA,
                    temperature=settings.google_model_temperature,
                    top_p=settings.google_model_top_p,
                    max_output_tokens=settings.google_model_max_tokens,
                ),
            )
            report_text = response.text
        except Exception as e:
            logger.error(f"[Moderator] Consensus generation failed: {e}")
            report_text = self._fallback_consensus(patient_context, risk_results)


        # Compute consensus score from agents' confidence values
        confidences = [t.get("confidence", 70) for t in full_transcript]
        consensus_score = round(sum(confidences) / len(confidences) / 100, 2) if confidences else 0.7

        return {
            "agent": "Moderator",
            "specialty": "MDT Consensus",
            "emoji": self.EMOJI,
            "round_type": "consensus",
            "consensus_report": report_text,
            "consensus_score": consensus_score,
            "argument": report_text,
            "confidence": int(consensus_score * 100),
            "priority_action": self._extract_priority(report_text),
        }

    @staticmethod
    def _format_transcript(transcript: list[dict]) -> str:
        lines = []
        for entry in transcript:
            emoji = entry.get("emoji", "🔬")
            agent = entry.get("agent", "Unknown")
            rtype = entry.get("round_type", "")
            conf = entry.get("confidence", "?")
            lines.append(
                f"{emoji} **{agent}** [{rtype}, confidence: {conf}%]\n"
                f"{entry.get('argument', '')}\n"
                f"*Priority Action:* {entry.get('priority_action', 'N/A')}"
            )
        return "\n\n---\n\n".join(lines)

    @staticmethod
    def _extract_priority(report: str) -> str:
        """Extract the first actionable recommendation from the report."""
        lines = report.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped and (stripped[0].isdigit() or stripped.startswith("-")):
                return stripped.lstrip("0123456789.-) ").strip()[:150]
        return "Comprehensive MDT follow-up within 4 weeks"

    def _fallback_consensus(
        self, ctx: dict[str, Any], risk: dict[str, Any]
    ) -> str:
        comp = risk.get("composite", {})
        return (
            f"## MDT Consensus Report\n\n"
            f"**Patient:** {ctx.get('age', '?')} y/o {ctx.get('gender', '?')}\n"
            f"**Composite Risk:** {comp.get('risk_percentage', '?')}% ({comp.get('risk_category', '?')})\n\n"
            f"The multi-disciplinary team has reviewed the available clinical data and ML risk predictions. "
            f"A comprehensive management plan addressing cardiovascular, metabolic, and lifestyle risk factors "
            f"is recommended. Follow-up within 4 weeks to review investigations and initiate appropriate therapy."
        )
