"""Pydantic schema validator for exact output compliance."""
from pydantic import BaseModel, Field, validator, ValidationError, model_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

class ValidationCategory(BaseModel):
    score: int = Field(default=0)
    max_score: int = Field(default=2)
    checks: Dict[str, Any] = Field(default_factory=dict)

class AuditEntry(BaseModel):
    step: str = Field(default="unknown")
    agent: str = Field(default="System")
    reasoning: str = Field(default="")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

class OutputSchema(BaseModel):
    invoice_id: str
    overall_decision: str = Field(..., pattern="^(APPROVED|REJECTED|ESCALATE_TO_HUMAN|HOLD_FOR_VERIFICATION)$")
    compliance_score: float = Field(default=0, ge=0, le=100)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    requires_human_review: bool = Field(default=False)
    validation_results: Dict[str, ValidationCategory] = Field(default_factory=dict)
    tds_summary: Dict[str, Any] = Field(default_factory=dict)
    gst_summary: Dict[str, Any] = Field(default_factory=dict)
    audit_trail: List[Union[AuditEntry, str, Dict]] = Field(default_factory=list)
    
    @model_validator(mode='before')
    @classmethod
    def normalize_input(cls, data: Any) -> dict:
        """Pre-process input to ensure required fields exist and audit_trail is normalized."""
        if not isinstance(data, dict):
            data = {}
        
        # Ensure required fields with defaults
        defaults = {
            "invoice_id": data.get("invoice_id", "UNKNOWN"),
            "overall_decision": data.get("overall_decision", "HOLD_FOR_VERIFICATION"),
            "compliance_score": data.get("compliance_score", 0),
            "confidence": data.get("confidence", 0.0),
            "requires_human_review": data.get("requires_human_review", True),
            "validation_results": data.get("validation_results", {
                "category_a_authenticity": {"score": 0, "max_score": 2, "checks": {}},
                "category_b_gst": {"score": 0, "max_score": 2, "checks": {}},
                "category_c_arithmetic": {"score": 0, "max_score": 2, "checks": {}},
                "category_d_tds": {"score": 0, "max_score": 2, "checks": {}},
                "category_e_policy": {"score": 0, "max_score": 2, "checks": {}}
            }),
            "tds_summary": data.get("tds_summary", {}),
            "gst_summary": data.get("gst_summary", {}),
            "audit_trail": data.get("audit_trail", [])
        }
        
        # Normalize audit_trail entries
        normalized_trail = []
        for entry in defaults["audit_trail"]:
            if isinstance(entry, str):
                normalized_trail.append(AuditEntry(step="note", agent="System", reasoning=entry).model_dump())
            elif isinstance(entry, dict):
                # Convert LLM-style entries ({timestamp, event, details}) to AuditEntry format
                if "event" in entry and "details" in entry:
                    normalized_trail.append({
                        "step": entry.get("event", "unknown"),
                        "agent": entry.get("agent", "Resolver"),
                        "reasoning": entry.get("details", ""),
                        "timestamp": entry.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                        "confidence": entry.get("confidence")
                    })
                else:
                    normalized_trail.append(AuditEntry(**{k: v for k, v in entry.items() if k in AuditEntry.model_fields}).model_dump())
            else:
                normalized_trail.append(AuditEntry().model_dump())
        
        defaults["audit_trail"] = normalized_trail
        return defaults
    
    @model_validator(mode='after')
    def validate_decision_confidence_alignment(self):
        """Ensure decision aligns with confidence threshold."""
        if self.confidence < 0.7 and self.overall_decision not in ["ESCALATE_TO_HUMAN", "HOLD_FOR_VERIFICATION"]:
            self.overall_decision = "ESCALATE_TO_HUMAN"
            self.requires_human_review = True
        return self

def validate_output_schema(data: dict) -> OutputSchema:
    """Validate and return parsed output schema with auto-correction."""
    try:
        return OutputSchema.model_validate(data)
    except ValidationError as e:
        # Try auto-correction with normalized input
        try:
            normalized = OutputSchema.normalize_input(data)
            return OutputSchema.model_validate(normalized)
        except:
            raise ValueError(f"Output schema validation failed: {e}")