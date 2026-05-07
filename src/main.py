#!/usr/bin/env python3
"""Main CLI entry point for Compliance Validator Agent."""
import os
import sys
import json
import re
import argparse
import logging
import warnings
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# ==============================================================================
# 1. SUPPRESS UNWANTED LOGS & WARNINGS
# ==============================================================================
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("opentelemetry").setLevel(logging.ERROR)
logging.getLogger("crewai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", message=".*method callbacks.*")
warnings.filterwarnings("ignore", message=".*TracerProvider.*")

# ==============================================================================
# 2. PATH SETUP & LOGGER INIT
# ==============================================================================
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from logging_config import logger
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

from src.agents.crew_pipeline import run_compliance_crew
from src.utils.schema_validator import validate_output_schema, OutputSchema

# ==============================================================================
# 3. DATA CLEANING & PARSING HELPERS
# ==============================================================================
def recursive_clean(obj: Any) -> Any:
    """Recursively strips whitespace from all string keys and values."""
    if isinstance(obj, dict):
        return {
            (k.strip() if isinstance(k, str) else k): recursive_clean(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [recursive_clean(item) for item in obj]
    elif isinstance(obj, str):
        return obj.strip()
    return obj

def parse_ocr_text_to_dict(text: str) -> Dict[str, Any]:
    """Regex-based extractor for PDF/Image OCR text."""
    data = {}
    if not text: return data
    
    # Common patterns for Indian invoices
    patterns = {
        "invoice_id": r"(?:Invoice\s*No|Invoice\s*ID|INV)[\s:]*([A-Z0-9\-/\.]+)",
        "vendor_gstin": r"([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1})",
        "total_amount": r"(?:Total|Grand\s*Total|Amount\s*Due)[\s₹:]*([\d,]+\.?\d*)",
        "invoice_date": r"(\d{2}[/-]\d{2}[/-]\d{4})"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            val = match.group(1).strip()
            if key == "total_amount":
                try: val = float(val.replace(",", ""))
                except: pass
            data[key] = val
            
    # Provide minimal fallback structure to prevent pipeline crashes
    data.setdefault("vendor", {"gstin": data.get("vendor_gstin", "")})
    data.setdefault("line_items", [])
    data.setdefault("total_amount", data.get("total_amount", 0))
    data.setdefault("invoice_date", data.get("invoice_date", datetime.now().strftime("%Y-%m-%d")))
    if "invoice_id" not in data:
        data["invoice_id"] = f"UNKNOWN_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return data

# ==============================================================================
# 4. MULTI-FORMAT INVOICE LOADER
# ==============================================================================
def load_invoices(input_path: str) -> list:
    """Load & normalize invoices from JSON, CSV, XML, PDF, or Image files."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    ext = path.suffix.lower()

    try:
        if ext == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return recursive_clean(data if isinstance(data, list) else [data])

        elif ext == ".csv":
            import pandas as pd
            df = pd.read_csv(path, dtype=str)
            return recursive_clean(df.to_dict(orient="records"))

        elif ext == ".xml":
            import xmltodict
            with open(path, "r", encoding="utf-8") as f:
                data = xmltodict.parse(f.read())
            root = data.get("root", data)
            invoices = root.get("invoices", root.get("invoice", []))
            if isinstance(invoices, dict): invoices = [invoices]
            return recursive_clean(invoices)

        elif ext == ".pdf":
            import pdfplumber
            invoices = []
            with pdfplumber.open(path) as pdf:
                full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                invoice_data = parse_ocr_text_to_dict(full_text)
                invoice_data["source_file"] = path.name
                invoices.append(invoice_data)
            return recursive_clean(invoices)

        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            from PIL import Image
            import pytesseract
            img = Image.open(path)
            text = pytesseract.image_to_string(img)
            invoice_data = parse_ocr_text_to_dict(text)
            invoice_data["source_file"] = path.name
            return recursive_clean([invoice_data])

        else:
            raise ValueError(f"Unsupported format: {ext}. Supported: .json, .csv, .xml, .pdf, .png, .jpg, .jpeg")
            
    except ImportError as e:
        raise ImportError(f"Missing dependency for {ext} format: {e}. Run: pip install pandas xmltodict pdfplumber pytesseract Pillow")
    except Exception as e:
        raise ValueError(f"Error loading {path.name}: {e}")

# ==============================================================================
# 5. MAIN EXECUTION LOOP
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Agentic AI Compliance Validator (Multi-Format)")
    parser.add_argument("--input", required=True, help="Path to invoice file (JSON, CSV, XML, PDF, Image)")
    parser.add_argument("--output", required=True, help="Path to output results JSON file")
    parser.add_argument("--split", action="store_true", help="Also save individual invoice results to results/ folder")
    args = parser.parse_args()
    
    logger.info("Starting compliance validation pipeline", input=args.input, output=args.output)
    
    try:
        invoices = load_invoices(args.input)
    except Exception as e:
        logger.error(f"Failed to load invoices: {e}")
        sys.exit(1)

    if not invoices:
        logger.error("No invoices found in input file.")
        print("❌ No invoices found.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(invoices)} clean invoices for processing")
    
    results = []
    batch_history = []
    results_dir = Path("results")
    if args.split:
        results_dir.mkdir(parents=True, exist_ok=True)
    
    for idx, invoice in enumerate(invoices, 1):
        # Get ID after cleaning (recursive_clean in load_invoices handles spaces)
        inv_id = invoice.get("invoice_id", f"UNKNOWN_{idx}")
        logger.info(f"Processing invoice {idx}/{len(invoices)}: {inv_id}")
        
        try:
            result = run_compliance_crew(invoice, batch_history)
            
            # Validate and Normalize Schema
            try:
                validated = validate_output_schema(result)
                final_output = validated.model_dump()
            except Exception:
                # Fallback if schema fails
                normalized = OutputSchema.normalize_input(result)
                final_output = validate_output_schema(normalized).model_dump()
            
            # Force correct invoice_id from input to prevent LLM hallucination
            final_output["invoice_id"] = inv_id
            
            # Final clean pass on output
            final_output = recursive_clean(final_output)
            
            results.append(final_output)
            
            # Update history for dedup logic
            key = f"{invoice.get('vendor',{}).get('gstin','')}|{invoice.get('invoice_number','')}|{invoice.get('total_amount',0)}"
            batch_history.append(key)
            
            # Save individual file if --split is enabled
            if args.split:
                safe_name = "".join(c if c.isalnum() else "_" for c in inv_id)
                individual_path = results_dir / f"{safe_name}_result.json"
                with open(individual_path, 'w', encoding='utf-8') as f:
                    json.dump(final_output, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved individual result: {individual_path}")
            
            decision = final_output.get("overall_decision", "UNKNOWN")
            print(f"✅ {inv_id}: {decision}")
            
        except Exception as e:
            logger.error(f"Failed to process {inv_id}: {str(e)}")
            print(f"⚠️ Error on {inv_id}: {str(e)}")
            # Append fallback result
            results.append({
                "invoice_id": inv_id,
                "overall_decision": "HOLD_FOR_VERIFICATION",
                "compliance_score": 0,
                "confidence": 0.0,
                "requires_human_review": True,
                "validation_results": {},
                "audit_trail": [{"step":"error","agent":"System","reasoning":str(e)}]
            })

    # Save consolidated results
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved consolidated results to {args.output}")

    # Summary
    approved = sum(1 for r in results if r.get('overall_decision') == 'APPROVED')
    rejected = sum(1 for r in results if r.get('overall_decision') == 'REJECTED')
    escalated = sum(1 for r in results if r.get('overall_decision') == 'ESCALATE_TO_HUMAN')
    held = sum(1 for r in results if r.get('overall_decision') == 'HOLD_FOR_VERIFICATION')
    
    print(f"\n📦 Results saved to {args.output}")
    print(f"📊 Summary: {approved} approved, {rejected} rejected, {escalated} escalated, {held} held")

if __name__ == "__main__":
    main()