# 🛡️ Compliance Validator Agent

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/VijaiVenkatesan/compliance-validator-agent)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/downloads/)
[![CrewAI 0.30](https://img.shields.io/badge/CrewAI-0.30-orange)](https://docs.crewai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Agentic AI Compliance Validator** — A multi-agent system that validates Indian GST invoices against statutory rules, company policies, and historical precedents using CrewAI orchestration, deterministic rule engines, and LLM-enhanced reasoning.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Groq API Key (or Gemini API Key)
- Tesseract OCR (for image/PDF support, optional)

### Installation
```bash
# Clone repository
git clone https://github.com/VijaiVenkatesan/compliance-validator-agent.git
cd compliance-validator-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

### Run the Validator

# Basic usage with JSON input
python src/main.py --input data/test_invoices.json --output results.json

# With multi-format support (PDF, CSV, XML, Images)
python src/main.py --input invoices/scan_001.pdf --output results.json

# Generate individual invoice reports
python src/main.py --input data/test_invoices.json --output results.json --split

### Environment Variables (.env)

# LLM Provider: groq | gemini
LLM_PROVIDER=groq

# API Keys
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Mock API (Optional)
USE_MOCK_API=false
MOCK_API_URL=http://localhost:8080

# Processing
CONFIDENCE_THRESHOLD=0.7
LLM_TEMPERATURE=0.05

🏗️ Architecture Overview

┌─────────────────────────────────────────────────┐
│                 CLI Interface                    │
│  src/main.py (--input, --output, --split)       │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Multi-Format Loader                 │
│  • JSON/CSV/XML: Direct parsing                 │
│  • PDF: pdfplumber + OCR extraction             │
│  • Images: pytesseract + regex normalization    │
│  • Recursive cleaning: Strip trailing spaces    │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│           4-Agent CrewAI Pipeline               │
│                                                 │
│  ┌─────────────┐  ┌─────────────┐              │
│  │  Extractor  │→│  Validator  │              │
│  │ (Normalize) │  │(10 Checks) │              │
│  └─────────────┘  └──────┬──────┘              │
│                         │                       │
│  ┌─────────────┐  ┌─────▼──────┐              │
│  │  Resolver   │→│  Reporter  │              │
│  │(Decide+Score)│  │(Schema Out)│              │
│  └─────────────┘  └────────────┘              │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│            Deterministic Rule Engines           │
│  • A1/A2: Invoice format & duplicate detection  │
│  • B1/B7: GSTIN validation & tax math          │
│  • C1/C2: Line arithmetic & subtotal checks    │
│  • D1/D2: TDS applicability & section mapping  │
│  • E1/E3: PO tolerance & approved vendor list  │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│           External Integrations (Optional)      │
│  • Mock GST API: GSTIN status, HSN rates       │
│  • Historical Decisions: Calibration (15% error guard)│
│  • Checks Manifest: Feature gating             │
└─────────────────────────────────────────────────┘

✅ Implemented Compliance Checks (10/10)

![alt text](image.png)

🎯 Decision Logic & Confidence Scoring
Decision Rules

if critical_failure:  # A1/B1 false, composition dealer, suspended vendor
    return "REJECTED", confidence=0.95+
elif checks_passed >= 89%:
    return "APPROVED", confidence=0.98
elif checks_passed >= 67%:
    return "ESCALATE_TO_HUMAN", confidence=0.65-0.75
else:
    return "REJECTED", confidence=0.85

Weighted Confidence Calculation

- Critical checks (A1, B1, B7, D1, E3): 80% weight, 1.5× penalty on failure
- Minor checks (A2, C1, C2, E1): 20% weight, 1× penalty
- Historical deviation: -0.15 confidence if overriding precedent
- Edge cases: Fixed confidence (0.85 for valid flags, 0.65 for ambiguous)

📊 Output Schema

{
  "invoice_id": "INV-2024-0001",
  "overall_decision": "APPROVED|REJECTED|ESCALATE_TO_HUMAN|HOLD_FOR_VERIFICATION",
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
        "A1_confidence": 0.99,
        "A2": true,
        "A2_finding": "✓ No duplicates detected",
        "A2_confidence": 0.98
      }
    }
    // ... categories b, c, d, e
  },
  "tds_summary": {
    "section": "194J",
    "rate": 10.0,
    "tds_on_gst": false
  },
  "gst_summary": {
    "intra_inter": "intra"
  },
  "audit_trail": [
    {
      "step": "validation",
      "agent": "Validator",
      "reasoning": "✓ Invoice format valid; ✓ GSTIN valid...",
      "timestamp": "2024-05-07T10:30:00Z",
      "confidence": 0.99
    }
  ]
}

🧪 Testing & Validation
Run Test Suite

# Validate against test invoices
python src/main.py --input data/test_invoices.json --output results_test.json

# Verify schema compliance
python -c "
import json
from src.utils.schema_validator import validate_output_schema
results = json.load(open('results_test.json'))
for r in results:
    validate_output_schema(r)
print('✅ All outputs schema-compliant')
"

# Check for trailing spaces (critical fix)
python -c "
import json
results = json.load(open('results_test.json'))
assert all(not k.endswith(' ') for r in results for k in r.keys()), 'Trailing spaces found!'
print('✅ No trailing spaces in output keys')
"

Expected Results Distribution

![alt text](image-1.png)

🔧 Development & Extensibility

Adding New Validation Checks

- Add function to src/tools/compliance_engines.py
- Update checks_manifest.json with new check ID
- Register in _execute_validation_tools() in crew_pipeline.py
- Add to _calculate_weighted_confidence() if critical

Supporting New File Formats

- Add format handler in load_invoices() in main.py
- Implement parse_ocr_text_to_dict() for unstructured data
- Ensure recursive_clean() is applied to output

Mock API Integration

# Start mock server (Terminal 1)
python mock_gst_server.py

# Enable in validator (Terminal 2)
$env:USE_MOCK_API="true"
python src/main.py --input data/test_invoices.json --output results.json

📦 Submission Package
Required Files
✅ README.md (this file)
✅ checks_manifest.json (10/10 checks implemented)
✅ requirements.txt (pinned dependencies)
✅ architecture.md (system design)
✅ analysis.md (results & edge cases)
✅ DEV_LOG.md (development history)
✅ src/main.py (CLI with --input/--output)
✅ reports/ folder with 3 sample outputs

📄 License
MIT License — See LICENSE for details.

🙏 Acknowledgments
CrewAI team for the agentic framework
Groq for ultra-fast LLM inference
Indian GST/TDS regulatory documentation
Challenge organizers for the comprehensive evaluation criteria

Repository: https://github.com/VijaiVenkatesan/compliance-validator-agent
Author: V VIJAI
Last Updated: 07th May 2026