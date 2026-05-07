# 🛡️ Compliance Validator Agent

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/VijaiVenkatesan/compliance-validator-agent)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/downloads/)
[![CrewAI 0.30](https://img.shields.io/badge/CrewAI-0.30-orange)](https://docs.crewai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Agentic AI Compliance Validator** — A multi-agent system that validates Indian GST invoices against statutory rules, company policies, and historical precedents using CrewAI orchestration, deterministic rule engines, and LLM-enhanced reasoning.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Groq API Key (or Gemini API Key)
- Tesseract OCR *(for image/PDF support — optional)*

### Installation

```bash
git clone https://github.com/VijaiVenkatesan/compliance-validator-agent.git
cd compliance-validator-agent
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Run the Validator

```bash
# Basic JSON input
python src/main.py --input data/test_invoices.json --output results.json

# Multi-format (PDF, CSV, XML, Images)
python src/main.py --input invoices/scan_001.pdf --output results.json

# Generate individual invoice reports
python src/main.py --input data/test_invoices.json --output results.json --split
```

### Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `groq` or `gemini` |
| `GROQ_API_KEY` | — | Groq API key |
| `GOOGLE_API_KEY` | — | Gemini API key |
| `USE_MOCK_API` | `false` | Enable mock GST API |
| `MOCK_API_URL` | `http://localhost:8080` | Mock server URL |
| `CONFIDENCE_THRESHOLD` | `0.7` | Minimum confidence to auto-approve |
| `LLM_TEMPERATURE` | `0.05` | LLM determinism setting |

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────┐
│            CLI Interface               │
│  src/main.py (--input, --output)       │
└──────────────────┬─────────────────────┘
                   │
┌──────────────────▼─────────────────────┐
│         Multi-Format Loader            │
│  JSON/CSV/XML · PDF · Images · OCR     │
│  + recursive_clean() on all input      │
└──────────────────┬─────────────────────┘
                   │
┌──────────────────▼─────────────────────┐
│        4-Agent CrewAI Pipeline         │
│                                        │
│  Extractor → Validator → Resolver      │
│                             ↓          │
│                          Reporter      │
└──────────────────┬─────────────────────┘
                   │
┌──────────────────▼─────────────────────┐
│      Deterministic Rule Engines        │
│  A1/A2 · B1/B7 · C1/C2 · D1/D2 · E1/E3│
└────────────────────────────────────────┘
```

---

## ✅ Compliance Checks (10/10 Implemented)

| Check | Category | Description |
|---|---|---|
| A1 | Authenticity | Invoice number format validation |
| A2 | Authenticity | Duplicate detection (±5% tolerance) |
| B1 | GST | GSTIN format + status validation |
| B7 | GST | Tax math: intra/inter-state + GTA/RCM |
| C1 | Arithmetic | Line-item amount calculation |
| C2 | Arithmetic | Subtotal + tax + grand total check |
| D1 | TDS | TDS applicability by service type |
| D2 | TDS | TDS section mapping (194C/194J/194I) |
| E1 | Policy | PO amount tolerance (±10%) |
| E3 | Policy | Approved vendor list verification |

---

## 🎯 Decision Logic & Confidence Scoring

```python
if critical_failure:          # A1/B1 false, composition dealer, suspended vendor
    return "REJECTED",        confidence=0.95+
elif checks_passed >= 89%:
    return "APPROVED",        confidence=0.85-0.98
elif checks_passed >= 67%:
    return "ESCALATE_TO_HUMAN", confidence=0.65
else:
    return "REJECTED",        confidence=0.85
```

**Confidence Weights:**
- Critical checks (A1, B1, B7, D1, E3): 80% weight, 1.5× failure penalty
- Minor checks (A2, C1, C2, E1): 20% weight, 1× failure penalty
- Historical deviation: −0.15 when overriding precedent

---

## 📊 Output Schema

```json
{
  "invoice_id": "INV-2024-0001",
  "overall_decision": "APPROVED",
  "compliance_score": 92.0,
  "confidence": 0.85,
  "requires_human_review": false,
  "validation_results": {
    "category_a_authenticity": {
      "score": 2,
      "max_score": 2,
      "checks": {
        "A1": true,
        "A1_finding": "✓ Valid invoice number format",
        "A1_confidence": 0.99
      }
    }
  },
  "tds_summary": { "section": "194J", "rate": 10.0, "tds_on_gst": false },
  "gst_summary": { "intra_inter": "intra" },
  "audit_trail": [...]
}
```

---

## 🧪 Testing & Validation

```bash
# Run full test suite
python src/main.py --input data/test_invoices.json --output results_test.json

# Verify schema compliance
python -c "
import json
from src.utils.schema_validator import validate_output_schema
results = json.load(open('results_test.json'))
for r in results: validate_output_schema(r)
print('✅ All outputs schema-compliant')
"

# Check for trailing spaces
python -c "
import json
results = json.load(open('results_test.json'))
assert all(not k.endswith(' ') for r in results for k in r.keys())
print('✅ No trailing spaces in output keys')
"
```

**Expected Results (21 invoices):**

| Decision | Count | % | Target |
|---|---|---|---|
| APPROVED | 10 | 47.6% | 50–60% |
| REJECTED | 6 | 28.6% | 20–30% |
| ESCALATE_TO_HUMAN | 5 | 23.8% | 10–20% |
| HOLD_FOR_VERIFICATION | 0 | 0% | <10% |

---

## 📦 Submission Checklist

- [x] `README.md`
- [x] `checks_manifest.json` (10/10 checks)
- [x] `requirements.txt`
- [x] `architecture.md`
- [x] `analysis.md`
- [x] `DEV_LOG.md`
- [x] `src/main.py`
- [x] `reports/` (3 sample outputs)

---

## 🔧 Extensibility

**Add a new check:**
1. Add function to `src/tools/compliance_engines.py`
2. Register in `checks_manifest.json`
3. Add to `_execute_validation_tools()` in `crew_pipeline.py`
4. Add to `_calculate_weighted_confidence()` if critical

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

**Repository:** https://github.com/VijaiVenkatesan/compliance-validator-agent  
**Author:** V VIJAI | **Last Updated:** 07 May 2026
