# Mock GST Portal API Documentation

## Base URL
```
http://localhost:8080/api/gst
```

## Authentication
All requests require header:
```
X-API-Key: test-api-key-12345
```

---

## Endpoints

### 1. Validate GSTIN

**POST** `/validate-gstin`

**Request:**
```json
{
  "gstin": "27AABCT1234F1ZP"
}
```

**Success Response (200):**
```json
{
  "valid": true,
  "gstin": "27AABCT1234F1ZP",
  "legal_name": "TechSoft Solutions Private Limited",
  "trade_name": "TechSoft",
  "status": "ACTIVE",
  "registration_date": "2019-04-15",
  "state_code": "27",
  "state": "Maharashtra",
  "taxpayer_type": "Regular",
  "constitution": "Private Limited Company",
  "last_return_filed": {
    "return_type": "GSTR-3B",
    "period": "September 2024",
    "filing_date": "2024-10-20"
  }
}
```

**Error Responses:**

*Invalid Format (400):*
```json
{
  "valid": false,
  "error": "INVALID_FORMAT",
  "message": "GSTIN must be 15 characters alphanumeric"
}
```

*Not Found (404):*
```json
{
  "valid": false,
  "error": "NOT_FOUND",
  "message": "GSTIN not registered in GST system"
}
```

*Suspended (200 with status):*
```json
{
  "valid": true,
  "gstin": "33AABCC1122P1ZW",
  "status": "SUSPENDED",
  "suspension_date": "2024-08-01",
  "suspension_reason": "Non-filing of returns for 6+ months"
}
```

*Cancelled (200 with status):*
```json
{
  "valid": true,
  "gstin": "XX...",
  "status": "CANCELLED",
  "cancellation_date": "2024-05-15",
  "cancellation_reason": "Voluntary cancellation"
}
```

---

### 2. Validate IRN

**POST** `/validate-irn`

**Request:**
```json
{
  "irn": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8"
}
```

**Success Response (200):**
```json
{
  "valid": true,
  "irn": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8",
  "status": "ACTIVE",
  "generation_date": "2024-09-15T10:30:00Z",
  "invoice_details": {
    "seller_gstin": "27AABCT1234F1ZP",
    "buyer_gstin": "27AABCF9999K1ZX",
    "invoice_number": "TS/MH/2024/001234",
    "invoice_date": "2024-09-15",
    "invoice_value": 590000
  }
}
```

**Error Responses:**

*Invalid IRN (404):*
```json
{
  "valid": false,
  "error": "IRN_NOT_FOUND",
  "message": "IRN does not exist in e-Invoice system"
}
```

*Cancelled IRN (200 with status):*
```json
{
  "valid": true,
  "irn": "...",
  "status": "CANCELLED",
  "cancellation_date": "2024-09-20",
  "cancellation_reason": "Invoice cancelled by seller"
}
```

---

### 3. Get HSN Rate

**GET** `/hsn-rate?code={hsn_code}&date={invoice_date}`

**Request:**
```
GET /hsn-rate?code=995411&date=2024-10-01
```

**Success Response (200):**
```json
{
  "hsn_sac": "995411",
  "description": "General construction services",
  "applicable_date": "2024-10-01",
  "rate": {
    "cgst": 6,
    "sgst": 6,
    "igst": 12
  },
  "effective_from": "2019-04-01",
  "notes": "Rate reduced from 18% w.e.f. 01-Apr-2019"
}
```

**Historical Rate (different date):**
```
GET /hsn-rate?code=995411&date=2019-03-15
```
```json
{
  "hsn_sac": "995411",
  "description": "General construction services",
  "applicable_date": "2019-03-15",
  "rate": {
    "cgst": 9,
    "sgst": 9,
    "igst": 18
  },
  "effective_from": "2017-07-01",
  "effective_to": "2019-03-31",
  "notes": "Original GST rate"
}
```

---

### 4. Check E-Invoice Requirement

**POST** `/e-invoice-required`

**Request:**
```json
{
  "seller_gstin": "27AABCT1234F1ZP",
  "invoice_date": "2024-10-01",
  "invoice_value": 590000
}
```

**Response (200):**
```json
{
  "required": true,
  "reason": "Seller turnover exceeds threshold",
  "seller_turnover_fy_prev": 85000000,
  "threshold": 50000000,
  "mandate_date": "2022-10-01"
}
```

---

### 5. Verify 206AB Status

**POST** `/verify-206ab`

**Request:**
```json
{
  "pan": "AXXPK5566Q"
}
```

**Response (200):**
```json
{
  "pan": "AXXPK5566Q",
  "section_206ab_applicable": true,
  "reason": "Non-filer of ITR for AY 2022-23 and AY 2023-24",
  "aggregate_tds_prev_fy": 85000,
  "verification_date": "2024-10-15"
}
```

---

## Rate Limiting

- 100 requests per minute per API key
- Exceeding limit returns 429 with `Retry-After` header

## Error Handling

All errors return:
```json
{
  "error": "ERROR_CODE",
  "message": "Human readable message",
  "timestamp": "2024-10-15T10:30:00Z"
}
```

## Mock Server Setup

To run the mock server:

```bash
# Install dependencies
pip install flask

# Run server
python mock_gst_server.py

# Server runs on localhost:8080
```

---

## Sample Mock Server Code

```python
# mock_gst_server.py
from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# Load mock data
with open('data/master_data/vendor_registry.json') as f:
    vendors = {v['gstin']: v for v in json.load(f)['vendors'] if v.get('gstin')}

@app.route('/api/gst/validate-gstin', methods=['POST'])
def validate_gstin():
    data = request.json
    gstin = data.get('gstin', '').upper().strip()
    
    # Basic format validation
    if len(gstin) != 15 or not gstin.isalnum():
        return jsonify({
            'valid': False,
            'error': 'INVALID_FORMAT',
            'message': 'GSTIN must be 15 characters alphanumeric'
        }), 400
    
    # Look up in mock data
    vendor = vendors.get(gstin)
    if not vendor:
        return jsonify({
            'valid': False,
            'error': 'NOT_FOUND',
            'message': 'GSTIN not registered in GST system'
        }), 404
    
    response = {
        'valid': True,
        'gstin': gstin,
        'legal_name': vendor['legal_name'],
        'trade_name': vendor.get('trade_name'),
        'status': vendor['status'],
        'state_code': vendor['state_code'],
        'state': vendor['state'],
        'taxpayer_type': vendor.get('gst_filing_status', 'Regular')
    }
    
    if vendor['status'] == 'SUSPENDED':
        response['suspension_date'] = vendor.get('suspension_date')
        response['suspension_reason'] = vendor.get('suspension_reason')
    
    return jsonify(response)

# Add other endpoints...

if __name__ == '__main__':
    app.run(port=8080, debug=True)
```

---

## Notes for Candidates

1. The mock server intentionally has some quirks to simulate real-world API behavior
2. Some requests may return slightly delayed responses (up to 2 seconds)
3. Rate limiting is enforced - implement proper retry logic
4. The server may return cached data - check timestamps
5. Not all GSTINs in test invoices exist in the mock - handle gracefully
