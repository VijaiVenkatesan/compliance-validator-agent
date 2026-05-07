"""Structured audit logging utility."""
import structlog
from datetime import datetime

logger = structlog.get_logger()

def log_agent_step(agent_name: str, invoice_id: str, step: str, result: dict, confidence: float = 1.0):
    """Log a single agent step with structured data."""
    logger.info(
        "agent_step",
        agent=agent_name,
        invoice_id=invoice_id,
        step=step,
        result=result,
        confidence=confidence,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )

def log_decision(invoice_id: str, decision: str, score: float, confidence: float, reasons: list):
    """Log final compliance decision."""
    logger.info(
        "compliance_decision",
        invoice_id=invoice_id,
        decision=decision,
        compliance_score=score,
        confidence=confidence,
        reasons=reasons,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )

def log_error(invoice_id: str, error: str, agent: str = "System"):
    """Log processing errors."""
    logger.error(
        "processing_error",
        invoice_id=invoice_id,
        error=error,
        agent=agent,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )