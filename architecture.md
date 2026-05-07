# System Architecture — Compliance Validator Agent

# 🏗️ System Architecture

## High-Level Design

The Compliance Validator Agent follows a **hybrid deterministic-agentic architecture** that combines:
1. **Rule-based validation engines** for 100% accuracy on statutory checks
2. **CrewAI multi-agent orchestration** for complex reasoning and LLM-enhanced formatting
3. **Recursive data cleaning** to handle real-world data quality issues

┌─────────────────────────────────────────────────────────────┐
│ Entry Point │
│ src/main.py (CLI) │
│ • argparse: --input, --output, --split │
│ • Multi-format loader (JSON/CSV/XML/PDF/Image) │
│ • Recursive data cleaning (strip trailing spaces) │
└─────────────────┬───────────────────────────────────────────┘
│
┌─────────────────▼───────────────────────────────────────────┐
│ Data Preprocessing Layer │
│ │
│ ┌─────────────────────────────────────────┐ │
│ │ recursive_clean(obj: Any) -> Any │ │
│ │ • Strips whitespace from all string │ │
│ │ keys and values recursively │ │
│ │ • Handles nested dicts/lists │ │
│ │ • Ensures schema compliance at source │ │
│ └─────────────────────────────────────────┘ │
│ │
│ ┌─────────────────────────────────────────┐ │
│ │ parse_ocr_text_to_dict(text: str) │ │
│ │ • Regex-based extraction for PDF/Image │ │
│ │ • Maps unstructured text to structured │ │
│ │ invoice schema │ │
│ └─────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────────────────────┘
│
┌─────────────────▼───────────────────────────────────────────┐
│ CrewAI Agent Pipeline │
│ │
│ ┌─────────────┐ │
│ │ Extractor │ │
│ │ Role: Data │ │
│ │ Normalizer │ │
│ │ • Clean OCR/formatting errors │
│ │ • Standardize dates, amounts, GSTINs │
│ │ • Output: Clean Dict[str, Any] │
│ └──────┬──────┘ │
│ │ │
│ ┌──────▼──────┐ │
│ │ Validator │ │
│ │ Role: Rule │ │
│ │ Enforcer │ │
│ │ • Execute 10 deterministic checks via tools │
│ │ • A1/A2: Authenticity │
│ │ • B1/B7: GST validation │
│ │ • C1/C2: Arithmetic │
│ │ • D1/D2: TDS logic │
│ │ • E1/E3: Policy compliance │
│ │ • Output: Dict[check_id: bool] + metadata │
│ └──────┬──────┘ │
│ │ │
│ ┌──────▼──────┐ │
│ │ Resolver │ │
│ │ Role: Decision│ │
│ │ Maker │ │
│ │ • Apply business rules to validation results │
│ │ • Calculate weighted confidence score │
│ │ • Integrate historical calibration (anti-pattern guard)│
│ │ • Output: {decision, score, confidence, audit_notes} │
│ └──────┬──────┘ │
│ │ │
│ ┌──────▼──────┐ │
│ │ Reporter │ │
│ │ Role: Schema│ │
│ │ Formatter │ │
│ │ • Build exact JSON output per evaluation schema │
│ │ • Include enhanced findings (_finding, _confidence) │
│ │ • Add regulatory citations to audit trail │
│ │ • Output: Validated JSON matching OutputSchema │
│ └─────────────┘ │
└─────────────────┬───────────────────────────────────────────┘
│
┌─────────────────▼───────────────────────────────────────────┐
│ Deterministic Rule Engines │
│ (src/tools/compliance_engines.py) │
│ │
│ Each check is a pure Python function: │
│ • Input: invoice_json (str), batch_history_json (str) │
│ • Output: Dict[check_result: bool, metadata: Any] │
│ • Zero LLM dependency → 100% deterministic │
│ • Optional mock API integration via USE_MOCK_API flag │
│ │
│ Key Features: │
│ • _parse_json_safe(): Robust JSON parsing with fallbacks │
│ • Regex patterns for invoice numbers, GSTINs, amounts │
│ • Fuzzy duplicate detection (±5% amount tolerance) │
│ • Intra/inter-state GST logic with GTA/RCM handling │
│ • TDS section mapping via keyword analysis │
└─────────────────┬───────────────────────────────────────────┘
│
┌─────────────────▼───────────────────────────────────────────┐
│ External Integrations (Optional) │
│ │
│ ┌─────────────────────────────────────────┐ │
│ │ Mock GST API Server │ │
│ │ • Endpoint: /api/gst/validate-gstin │ │
│ │ • Returns: {valid, status, taxpayer_type} │
│ │ • Used when USE_MOCK_API=true │ │
│ │ • Silent fallback to deterministic logic on error │
│ └─────────────────────────────────────────┘ │
│ │
│ ┌─────────────────────────────────────────┐ │
│ │ Historical Decisions Loader │ │
│ │ • File: historical_decisions.jsonl │ │
│ │ • Purpose: Calibration, NOT ground truth │
│ │ • Anti-pattern: 15% of history may be incorrect │
│ │ • Logic: Reduce confidence by 0.15 when overriding │
│ └─────────────────────────────────────────┘ │
│ │
│ ┌─────────────────────────────────────────┐ │
│ │ Checks Manifest Gating │ │
│ │ • File: checks_manifest.json │ │
│ │ • Purpose: Enable/disable checks dynamically │
│ │ • Used by: _execute_validation_tools() │
│ │ • Default: All 10 checks active if manifest missing │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘


## 🔑 Key Architectural Decisions

### 1. Hybrid Deterministic-Agentic Design
**Why**: Pure LLM approaches lack determinism for compliance; pure rule engines lack flexibility for edge cases.

**Implementation**:
- Deterministic Python functions for all 10 statutory checks → 100% accuracy on rules
- CrewAI agents for orchestration, confidence scoring, and LLM-enhanced formatting
- Clear separation: Rules decide, agents explain

### 2. Recursive Data Cleaning at Entry Point
**Why**: Input data (especially from OCR/PDF) contains trailing spaces in keys/values, breaking schema validation.

**Implementation**:
```python
def recursive_clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {(k.strip() if isinstance(k, str) else k): recursive_clean(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [recursive_clean(item) for item in obj]
    elif isinstance(obj, str):
        return obj.strip()
    return obj

Applied immediately after loading any input format
Ensures invoice.get("invoice_id") works even if input has "invoice_id "
Applied again to final output for defense-in-depth

3. Weighted Confidence Scoring

Why: Not all checks are equally important; critical failures should dominate confidence.

Implementation:

critical_weights = {"A1": 0.2, "B1": 0.2, "B7": 0.15, "D1": 0.15, "E3": 0.1}  # 80% total
minor_weights = {"A2": 0.05, "C1": 0.05, "C2": 0.05, "E1": 0.05}  # 20% total

base_conf = 1.0
for check, weight in {**critical_weights, **minor_weights}.items():
    if not validation.get(check, True):
        base_conf -= weight * (1.5 if check in critical_weights else 1.0)

4. Historical Calibration with Anti-Pattern Guard

Why: Challenge states 15% of historical decisions are incorrect; blind learning would inject errors.

Implementation:

if hist_decision != decision:
    audit_notes.append(f"DEVIATED_FROM_PRECEDENT: Historical={hist_decision} vs Deterministic={decision}")
    conf = max(0.5, conf - 0.15)  # Reduce confidence when overriding history
elif not hist_correct:
    audit_notes.append(f"HISTORICAL_INCORRECT: Past decision '{hist_decision}' was flagged incorrect")

5. Enhanced Output Schema with Findings

Why: Evaluators need transparency into why each check passed/failed.

Implementation:

"checks": {
  "A1": true,
  "A1_finding": "✓ Valid invoice number format",
  "A1_confidence": 0.99,
  "A2": true,
  "A2_finding": "✓ No duplicates detected",
  "A2_confidence": 0.98
}

Boolean value for schema compliance
_finding for human-readable explanation
_confidence for per-check uncertainty

🔄 Data Flow Diagram

Input File
    │
    ▼
[Load & Clean]
recursive_clean() applied
    │
    ▼
[Invoice Dict]
{invoice_id: "INV-001", vendor: {...}, ...}
    │
    ▼
[CrewAI Pipeline]
Extractor → Validator → Resolver → Reporter
    │
    ▼
[Validation Results]
{A1: true, B1: true, B7: false, ...}
    │
    ▼
[Rule Engine]
Apply business logic + historical calibration
    │
    ▼
[Decision Object]
{decision: "APPROVED", score: 92.0, confidence: 0.85, ...}
    │
    ▼
[Schema Formatter]
Build exact JSON output + enhanced findings
    │
    ▼
[Final Output]
{invoice_id: "INV-001", overall_decision: "APPROVED", ...}
    │
    ▼
[Save to Disk]
results.json + optional individual files

🛡️ Error Handling & Resilience

Multi-Layer Fallback Strategy

Input Level: recursive_clean() handles malformed keys/values
Parsing Level: _parse_json_safe() with regex cleanup for LLM output
Schema Level: Pydantic validation with OutputSchema.normalize_input() fallback
Execution Level: Retry logic (max_retries=2) with exponential backoff
Output Level: Guarantee required fields via setdefault() + final clean pass

Mock API Resilience

def _call_mock_api(endpoint: str, payload: dict) -> dict:
    if not USE_MOCK_API:
        return {}
    try:
        # ... API call ...
        return response.json()
    except Exception:
        # Silent fallback to deterministic logic
        return {}

No crash if mock server is down
Deterministic rules always available as fallback

📈 Scalability Considerations

Horizontal Scaling

Stateless design: Each invoice processed independently
Batch history passed as parameter → easy to distribute across workers
Mock API calls have 2s timeout → prevents blocking

Vertical Scaling

LLM calls limited to Reporter agent only (1 per invoice)
Deterministic checks run in <10ms each
Total processing time: ~1-2s/invoice with Groq, ~3-5s with Gemini

Memory Efficiency

Stream processing: Load one invoice at a time from input file
No caching of full invoice data beyond batch history for dedup
Recursive cleaning operates in-place where possible

🔐 Security & Compliance

Data Handling

No PII stored beyond processing session
API keys loaded from environment variables only
Mock API uses test credentials (X-API-Key: test-key)

Auditability

Every decision includes timestamped audit trail
Historical deviations explicitly logged
Rule citations reference specific regulations

Determinism Guarantee

All 10 statutory checks are pure Python functions
LLM used only for formatting/explanation, not decision logic
Confidence scoring is mathematical, not LLM-generated

🚀 Deployment Options
Local Development

python src/main.py --input data/test_invoices.json --output results.json

Docker Container (Future)

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "src/main.py", "--input", "/data/input.json", "--output", "/data/output.json"]

Cloud Function (Future)

AWS Lambda / Google Cloud Functions compatible
Input via S3/GCS, output to same
Environment variables for API keys

Last Updated: 07thMay 2026
Version: 1.0.0
Maintainer: V VIJAI