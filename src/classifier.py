"""
AI Ticket Classification Engine for Vireo Audio Support Desk.
Provides hybrid classification:
1. High-precision semantic and contextual scoring engine (Zero-dependency, offline).
2. LLM-assisted inference (OpenAI / Gemini compatible) for deep ambiguity resolution.
Outputs structured JSON with predicted category, confidence score, evidence quote,
uncertainty flag, and suggested routing team.
"""

import re
import os
import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    ticket_id: Optional[str] = None
    predicted_category: str
    confidence: float
    evidence_quote: str
    uncertainty_flag: bool
    suggested_routing_team: str
    routing_reason: str


# Team routing mapping based on category
CATEGORY_TO_TEAM = {
    "Billing & Payments": "Billing",
    "Delivery & Shipping": "Logistics",
    "Returns & Refunds": "Returns Desk",
    "Warranty & Repair": "Escalations & Warranty",
    "Connectivity": "Chat Frontline",
    "Charging & Battery": "Chat Frontline",
    "App & Firmware": "Chat Frontline",
    "Audio Quality": "Chat Frontline",
    "Product Enquiry": "Chat Frontline",
    "Account & Login": "Chat Frontline",
    "Other": "Chat Frontline"
}


class SemanticRuleClassifier:
    """
    Precision-targeted contextual semantic classifier.
    Resolves the critical 'Billing Illusion':
    Disentangles delivery delays mentioning payment terms from genuine billing disputes,
    while respecting initial intake tags where no contradiction exists.
    """

    DELIVERY_PATTERNS = [
        r"\b(courier|tracking|track|awb|dispatch|shipment|shipping|transit|rto|door|delivered|delivery|reach|package|box)\b",
        r"\b(not received|haven'?t received|where is|still waiting|nothing in hand|delayed|delay|lost in transit|damaged)\b",
        r"\b(nothing.*door|item not with me|re-shipped|order not delivered|5 days and counting)\b"
    ]

    GENUINE_BILLING_PATTERNS = [
        r"\b(charged twice|double deduction|debited twice|extra deduction|invoice|gst|gstin|tax invoice)\b",
        r"\b(payment failed|debited but no order|no order was created|failed transaction|unauthorized)\b",
        r"\b(bank statement|transaction id|utr|payment error|gateway error|bill with my firm)\b"
    ]

    RETURNS_PATTERNS = [
        r"\b(refund.*bank|refund promised|refund not credited|money back|return request|send back)\b",
        r"\b(return|exchange|qc failed|pickup for return|reversal of amount|refund status)\b"
    ]

    WARRANTY_PATTERNS = [
        r"\b(warranty claim|warranty|repair|service center|manufacturing defect|within warranty|rma)\b",
        r"\b(stopped working after \d+ months|strap pin|hardware failure|replace under warranty)\b"
    ]

    def classify(self, message: str, initial_category: Optional[str] = None, ticket_id: Optional[str] = None) -> ClassificationResult:
        text = str(message).lower().strip()
        bot_cat = initial_category or "Other"

        # Check for Delivery vs Billing signals
        is_delivery = False
        delivery_evidence = ""
        for pat in self.DELIVERY_PATTERNS:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                is_delivery = True
                delivery_evidence = match.group(0)
                break

        is_billing = False
        billing_evidence = ""
        for pat in self.GENUINE_BILLING_PATTERNS:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                is_billing = True
                billing_evidence = match.group(0)
                break

        # Check for Returns signals
        is_return = False
        return_evidence = ""
        for pat in self.RETURNS_PATTERNS:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                is_return = True
                return_evidence = match.group(0)
                break

        # Core Disambiguation Logic:
        # If bot tagged as Billing & Payments, but customer complains of missing delivery/tracking
        if bot_cat == "Billing & Payments":
            if is_delivery and not is_billing:
                predicted = "Delivery & Shipping"
                evidence = delivery_evidence
                confidence = 0.92
                uncertain = False
                reason = f"Override: Delivery/tracking complaint '{evidence}' misclassified by intake bot as Billing."
            elif is_return and not is_billing:
                predicted = "Returns & Refunds"
                evidence = return_evidence
                confidence = 0.88
                uncertain = False
                reason = f"Override: Refund/return request '{evidence}' misclassified by intake bot as Billing."
            elif is_billing:
                predicted = "Billing & Payments"
                evidence = billing_evidence
                confidence = 0.95
                uncertain = False
                reason = f"Confirmed genuine billing dispute via '{evidence}'."
            else:
                # Ambiguous billing mention
                predicted = "Billing & Payments"
                evidence = text[:40]
                confidence = 0.65
                uncertain = True
                reason = "Preserved billing tag with low confidence; flag for agent review."

        elif is_delivery and bot_cat in ["Other", "Product Enquiry"]:
            predicted = "Delivery & Shipping"
            evidence = delivery_evidence
            confidence = 0.90
            uncertain = False
            reason = f"Detected shipment tracking intent '{evidence}'."

        elif is_billing and bot_cat in ["Other", "Product Enquiry"]:
            predicted = "Billing & Payments"
            evidence = billing_evidence
            confidence = 0.90
            uncertain = False
            reason = f"Detected billing/invoice intent '{evidence}'."

        else:
            # Retain bot baseline for standard frontline technical categories
            predicted = bot_cat
            evidence = text[:40] if text else "Intake signal"
            confidence = 0.85
            uncertain = False
            reason = f"Preserved baseline categorization ({bot_cat}) aligned with frontline queue."

        routing_team = CATEGORY_TO_TEAM.get(predicted, "Chat Frontline")

        return ClassificationResult(
            ticket_id=ticket_id,
            predicted_category=predicted,
            confidence=confidence,
            evidence_quote=evidence,
            uncertainty_flag=uncertain,
            suggested_routing_team=routing_team,
            routing_reason=reason
        )


class LLMClassifier:
    """
    LLM-powered classifier using OpenAI or Gemini API if available.
    Falls back gracefully to SemanticRuleClassifier if keys are not present.
    """

    def __init__(self):
        self.rule_engine = SemanticRuleClassifier()
        self.api_type = self._detect_api()

    def _detect_api(self) -> Optional[str]:
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        elif os.getenv("GEMINI_API_KEY"):
            return "gemini"
        return None

    def classify(self, message: str, initial_category: Optional[str] = None, ticket_id: Optional[str] = None) -> ClassificationResult:
        if not self.api_type:
            return self.rule_engine.classify(message, initial_category=initial_category, ticket_id=ticket_id)

        try:
            if self.api_type == "openai":
                return self._call_openai(message, initial_category, ticket_id)
            elif self.api_type == "gemini":
                return self._call_gemini(message, initial_category, ticket_id)
        except Exception:
            return self.rule_engine.classify(message, initial_category=initial_category, ticket_id=ticket_id)

    def _call_openai(self, message: str, initial_category: Optional[str], ticket_id: Optional[str]) -> ClassificationResult:
        from openai import OpenAI
        client = OpenAI()
        prompt = self._build_prompt(message, initial_category)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        data = json.loads(response.choices[0].message.content)
        category = data.get("predicted_category", initial_category or "Other")
        confidence = float(data.get("confidence", 0.85))
        evidence = data.get("evidence_quote", message[:40])
        routing = CATEGORY_TO_TEAM.get(category, "Chat Frontline")
        return ClassificationResult(
            ticket_id=ticket_id,
            predicted_category=category,
            confidence=confidence,
            evidence_quote=evidence,
            uncertainty_flag=confidence < 0.75,
            suggested_routing_team=routing,
            routing_reason=data.get("reasoning", "LLM categorization")
        )

    def _call_gemini(self, message: str, initial_category: Optional[str], ticket_id: Optional[str]) -> ClassificationResult:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = self._build_prompt(message, initial_category)
        resp = model.generate_content(prompt)
        text = resp.text.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(text)
        category = data.get("predicted_category", initial_category or "Other")
        confidence = float(data.get("confidence", 0.85))
        evidence = data.get("evidence_quote", message[:40])
        routing = CATEGORY_TO_TEAM.get(category, "Chat Frontline")
        return ClassificationResult(
            ticket_id=ticket_id,
            predicted_category=category,
            confidence=confidence,
            evidence_quote=evidence,
            uncertainty_flag=confidence < 0.75,
            suggested_routing_team=routing,
            routing_reason=data.get("reasoning", "Gemini categorization")
        )

    def _build_prompt(self, message: str, initial_category: Optional[str]) -> str:
        cats_str = ", ".join(CATEGORY_TO_TEAM.keys())
        return f"""You are a customer support ticket categorizer for Vireo Audio.
Given the customer's message, classify it into exactly ONE of the following categories:
{cats_str}

Initial Bot Tag: {initial_category or 'None'}

Key Rule:
- If customer says "I paid X days ago, nothing arrived / where is order", the issue is 'Delivery & Shipping', NOT 'Billing & Payments'.
- 'Billing & Payments' is strictly for double deductions, invoice/GST requests, or gateway transaction errors.

Output ONLY a JSON object:
{{
  "predicted_category": "<category>",
  "confidence": <float 0.0 to 1.0>,
  "evidence_quote": "<quote>",
  "reasoning": "<1 sentence explanation>"
}}

Customer Message:
"{message}"
"""


# Global classifier instance
classifier = SemanticRuleClassifier()


def classify_ticket(message: str, initial_category: Optional[str] = None, ticket_id: Optional[str] = None) -> ClassificationResult:
    """Convenience function to classify a single ticket message."""
    return classifier.classify(message, initial_category=initial_category, ticket_id=ticket_id)
