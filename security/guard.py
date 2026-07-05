"""
Clinical Privacy & Prompt Guard Security Module.

Provides:
  1. PHI Anonymizer: Masking patient names, emails, phones, and identifiers.
  2. Prompt Guard: Detection of adversarial prompt injection attempts.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)

# Basic patterns for PHI (Protected Health Information) detection
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
ZIP_REGEX = re.compile(r"\b\d{5}(-\d{4})?\b")


class ClinicalSecurityGuard:
    """Manages PHI redaction and prompt injection checks for LLM safety."""

    def __init__(self):
        self.phi_enabled = settings.phi_masking_enabled
        self.guard_enabled = settings.prompt_guard_enabled
        self.threshold = settings.prompt_guard_threshold

    def anonymize_phi(self, text: str, patient_name: Optional[str] = None) -> str:
        """
        Redact Protected Health Information (PHI) from clinical text.

        Args:
            text: Raw clinical text / notes.
            patient_name: Optional name of the patient to specifically redact.

        Returns:
            Anonymized string with PII replaced by tokens.
        """
        if not self.phi_enabled or not text:
            return text

        anonymized = text

        # 1. Mask common PII patterns first (so names inside emails are captured as [EMAIL])
        anonymized = EMAIL_REGEX.sub("[EMAIL]", anonymized)
        anonymized = PHONE_REGEX.sub("[PHONE_NUMBER]", anonymized)
        anonymized = SSN_REGEX.sub("[IDENTIFIER]", anonymized)

        # 2. Mask explicit patient name if provided
        if patient_name:
            # Match first, last, and full name case-insensitively
            name_parts = [p.strip() for p in patient_name.split() if len(p.strip()) > 2]
            for part in name_parts:
                pattern = re.compile(re.escape(part), re.IGNORECASE)
                anonymized = pattern.sub("[PATIENT_NAME]", anonymized)
            
            pattern_full = re.compile(re.escape(patient_name), re.IGNORECASE)
            anonymized = pattern_full.sub("[PATIENT_NAME]", anonymized)
        
        # 3. Try Presidio if imported (advanced NLP fallback)
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            
            analyzer = AnalyzerEngine()
            anonymizer = AnonymizerEngine()
            
            results = analyzer.analyze(
                text=anonymized, 
                language=settings.phi_presidio_language or "en",
                entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "US_SSN", "LOCATION"]
            )
            anonymized = anonymizer.anonymize(text=anonymized, analyzer_results=results).text
        except Exception:
            # Fall back to standard regex masks
            pass

        return anonymized

    def is_prompt_injection(self, prompt: str) -> tuple[bool, float, str]:
        """
        Scan a prompt for malicious instruction override attempts.

        Returns:
            Tuple of (is_flagged, score, reason).
        """
        if not self.guard_enabled or not prompt:
            return False, 0.0, "Disabled"

        injection_indicators = [
            r"ignore\s+(previous|prior)\s+instructions",
            r"system\s+prompt\s+bypass",
            r"you\s+are\s+now\s+a",
            r"forget\s+everything\s+you",
            r"acting\s+as\s+a",
            r"developer\s+mode",
            r"jailbreak",
        ]

        score = 0.0
        matched = []
        for pattern in injection_indicators:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                score += 0.4
                matched.append(match.group(0))

        is_flagged = score >= self.threshold or len(matched) >= 2
        reason = f"Adversarial patterns detected: {', '.join(matched)}" if is_flagged else "Clear"
        
        if is_flagged:
            logger.warning(f"[Security] Blocked potential prompt injection: {reason}")

        return is_flagged, min(1.0, score), reason
