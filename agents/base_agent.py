"""
Base Clinical Agent.

All specialist agents inherit from this class.
Provides structured debate turn generation using Gemini via google-genai.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from google import genai
from google.genai import types

from config.settings import settings

logger = logging.getLogger(__name__)

# Configure Gemini client once at module load
_CLIENT: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _CLIENT
    if _CLIENT is None:
        api_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "GOOGLE_API_KEY is not set. Add it to your .env file."
            )
        _CLIENT = genai.Client(api_key=api_key)
    return _CLIENT


def _ensure_configured() -> None:
    """Alias for backwards-compatibility used in moderator."""
    _get_client()


class ClinicalAgent:
    """
    Base class for all specialist clinical debate agents.

    Each agent has a specialty, persona, and a system prompt that defines
    its clinical perspective during the debate.
    """

    # Subclasses set these
    SPECIALTY: str = "General"
    PERSONA: str = "You are a helpful clinical AI assistant."
    EMOJI: str = "🏥"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.google_model
        self._client = _get_client()

    def generate_opening_argument(
        self,
        patient_context: dict[str, Any],
        risk_results: dict[str, Any],
        rag_context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Generate the agent's opening argument for the debate.

        Args:
            patient_context: Patient summary dict
            risk_results: Output from inference.predict_all_risks()
            rag_context: Optional retrieved clinical guidelines

        Returns:
            Structured argument dict
        """
        prompt = self._build_opening_prompt(patient_context, risk_results, rag_context)
        return self._call(prompt, round_type="opening")

    def generate_rebuttal(
        self,
        patient_context: dict[str, Any],
        risk_results: dict[str, Any],
        prior_arguments: list[dict[str, Any]],
        rag_context: Optional[str] = None,
    ) -> dict[str, Any]:
        """Generate a rebuttal to prior arguments from other specialists."""
        prompt = self._build_rebuttal_prompt(
            patient_context, risk_results, prior_arguments, rag_context
        )
        return self._call(prompt, round_type="rebuttal")

    def generate_closing(
        self,
        patient_context: dict[str, Any],
        debate_so_far: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate a closing statement with final recommendation."""
        prompt = self._build_closing_prompt(patient_context, debate_so_far)
        return self._call(prompt, round_type="closing")

    # ─── Prompt builders ─────────────────────────────────────────────────────

    def _build_patient_summary(self, ctx: dict[str, Any], risk: dict[str, Any]) -> str:
        lines = [
            f"**Patient:** {ctx.get('age', '?')} y/o {ctx.get('gender', '?')}",
            f"**BMI:** {ctx.get('bmi', 'N/A')}",
            f"**Active Conditions:** {', '.join(ctx.get('active_conditions', [])) or 'None'}",
            f"**Medications:** {', '.join(ctx.get('active_medications', [])) or 'None'}",
            f"**Allergies:** {', '.join(ctx.get('allergies', [])) or 'None'}",
            "",
            "**Risk Scores:**",
            f"  - Cardiovascular: {risk['cardiovascular']['risk_percentage']}% ({risk['cardiovascular']['risk_category']})",
            f"  - Diabetes: {risk['diabetes']['risk_percentage']}% ({risk['diabetes']['risk_category']})",
            f"  - Composite: {risk['composite']['risk_percentage']}% ({risk['composite']['risk_category']})",
            "",
            "**Top Risk Factors:**",
        ]
        for f in risk.get("top_risk_factors", []):
            lines.append(f"  - {f['feature']}: value={f['value']}, contribution={f['contribution']}")
        return "\n".join(lines)

    def _build_opening_prompt(
        self, ctx: dict, risk: dict, rag: Optional[str]
    ) -> str:
        patient_txt = self._build_patient_summary(ctx, risk)
        guideline_txt = f"\n\n**Relevant Guidelines:**\n{rag}" if rag else ""
        return (
            f"You are participating in a multi-disciplinary clinical debate as a {self.SPECIALTY} specialist.\n\n"
            f"=== PATIENT DATA ===\n{patient_txt}{guideline_txt}\n\n"
            "=== TASK ===\n"
            f"Provide your opening argument from a {self.SPECIALTY} perspective. Address:\n"
            "1. The primary risk concerns from your specialty\n"
            "2. What the ML risk scores indicate from your viewpoint\n"
            "3. Your initial diagnostic hypothesis\n"
            "4. Recommended immediate investigations or actions\n\n"
            "Be specific, cite clinical evidence where possible, and quantify your confidence (0-100%).\n"
            "Format: [ARGUMENT] your argument [/ARGUMENT]\n"
            "[CONFIDENCE] 0-100 [/CONFIDENCE]\n"
            "[PRIORITY_ACTION] single most important action [/PRIORITY_ACTION]"
        )

    def _build_rebuttal_prompt(
        self, ctx: dict, risk: dict, prior: list[dict], rag: Optional[str]
    ) -> str:
        patient_txt = self._build_patient_summary(ctx, risk)
        prior_txt = "\n\n".join([
            f"**{a['agent']} ({a['specialty']}):**\n{a['argument']}"
            for a in prior if a.get("agent") != self.SPECIALTY
        ])
        guideline_txt = f"\n\n**Guidelines:**\n{rag}" if rag else ""
        return (
            f"You are the {self.SPECIALTY} specialist in a clinical debate.\n\n"
            f"=== PATIENT DATA ===\n{patient_txt}{guideline_txt}\n\n"
            f"=== PRIOR ARGUMENTS ===\n{prior_txt}\n\n"
            "=== TASK ===\n"
            "Provide your rebuttal. Address:\n"
            "1. Points from other specialists you agree with and why\n"
            "2. Points you disagree with and your counter-evidence\n"
            "3. Risks or factors the other specialists may have underweighted\n"
            "4. Updated recommendation after hearing other perspectives\n\n"
            "Format: [ARGUMENT] your argument [/ARGUMENT]\n"
            "[CONFIDENCE] 0-100 [/CONFIDENCE]\n"
            "[PRIORITY_ACTION] single most important action [/PRIORITY_ACTION]"
        )

    def _build_closing_prompt(self, ctx: dict, debate: list[dict]) -> str:
        debate_txt = "\n\n".join([
            f"**Round {d.get('round', '?')} — {d['agent']} ({d['specialty']}):**\n{d['argument']}"
            for d in debate
        ])
        return (
            f"You are the {self.SPECIALTY} specialist providing a closing statement.\n\n"
            f"=== FULL DEBATE TRANSCRIPT ===\n{debate_txt}\n\n"
            "=== TASK ===\n"
            "Provide your final position:\n"
            "1. Your definitive recommendation from your specialty\n"
            "2. How the debate changed (or confirmed) your initial view\n"
            "3. Outstanding concerns that need monitoring\n\n"
            "Format: [ARGUMENT] your closing statement [/ARGUMENT]\n"
            "[CONFIDENCE] 0-100 [/CONFIDENCE]\n"
            "[PRIORITY_ACTION] single most important action [/PRIORITY_ACTION]"
        )

    # ─── LLM call ────────────────────────────────────────────────────────────

    def _call(self, prompt: str, round_type: str) -> dict[str, Any]:
        """Call the Gemini model and parse the structured response."""
        try:
            from security.guard import ClinicalSecurityGuard
            guard = ClinicalSecurityGuard()
            prompt = guard.anonymize_phi(prompt)
        except Exception as e:
            logger.debug(f"PHI anonymization skipped: {e}")

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
            text = response.text
        except Exception as e:
            logger.error(f"[{self.SPECIALTY}] LLM call failed: {e}")
            text = self._fallback_response(round_type)

        argument = self._extract_tag(text, "ARGUMENT")
        confidence_raw = self._extract_tag(text, "CONFIDENCE")
        priority_action = self._extract_tag(text, "PRIORITY_ACTION")

        try:
            confidence = min(100, max(0, int(confidence_raw.strip())))
        except (ValueError, AttributeError):
            confidence = 70

        return {
            "agent": self.SPECIALTY,
            "specialty": self.SPECIALTY,
            "emoji": self.EMOJI,
            "round_type": round_type,
            "argument": argument or text,
            "confidence": confidence,
            "priority_action": priority_action or "Further evaluation needed",
            "raw_response": text,
        }

    @staticmethod
    def _extract_tag(text: str, tag: str) -> Optional[str]:
        import re
        pattern = rf"\[{tag}\](.*?)\[/{tag}\]"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _fallback_response(self, round_type: str) -> str:
        return (
            f"[ARGUMENT] As the {self.SPECIALTY} specialist, I need more clinical data "
            f"to provide a definitive {round_type}. Based on available information, "
            f"comprehensive assessment is recommended. [/ARGUMENT]\n"
            "[CONFIDENCE] 50 [/CONFIDENCE]\n"
            "[PRIORITY_ACTION] Comprehensive clinical assessment [/PRIORITY_ACTION]"
        )
