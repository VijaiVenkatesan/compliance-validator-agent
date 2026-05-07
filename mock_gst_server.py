"""Mock GST Portal API Server — Simulates realistic API behavior for testing."""
from flask import Flask, request, jsonify
from datetime import datetime
import json, os, time, random

app = Flask(__name__)

# Load mock vendor registry
def load_vendors():
    path = os.path.join(os.path.dirname(__file__), "data", "vendor_registry.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
            return {v['gstin']: v for v in data.get('vendors', []) if v.get('gstin')}
    # Fallback minimal registry
    return {
        "27AABCT1234F1ZP": {"name": "TechSoft Solutions", "status": "ACTIVE", "type": "Regular", "pan": "AABCT1234F"},
        "07AABCG5678H1Z9": {"name": "Global Logistics", "status": "ACTIVE", "type": "GTA", "pan": "AABCG5678H"},
        "33AABCC1122P1ZW": {"name": "Chennai Software", "status": "SUSPENDED", "type": "Regular", "pan": "AABCC1122P", "suspension_date": "2024-08-01"},
        "27AXXPK5566Q1ZB": {"name": "RK Electricals", "status": "ACTIVE", "type": "Regular", "pan": "AXXPK5566Q"},
        "27AABCP7788R1ZT": {"name": "Prime Real Estate", "status": "ACTIVE", "type": "Regular", "pan": "AABCP7788R"},
        "27AABCF9999K1ZX": {"name": "FinanceGuard Solutions", "status": "ACTIVE", "type": "Regular", "pan": "AABCF9999K"},
    }

VENDORS = load_vendors()

@app.route('/api/gst/validate-gstin', methods=['POST'])
def validate_gstin():
    """Validate GSTIN format and status."""
    data = request.json or {}
    gstin = data.get('gstin', '').upper().strip()
    
    # Format validation
    if len(gstin) != 15 or not gstin.isalnum():
        return jsonify({
            'valid': False, 'error': 'INVALID_FORMAT',
            'message': 'GSTIN must be 15 characters alphanumeric'
        }), 400
    
    # Lookup
    vendor = VENDORS.get(gstin)
    if not vendor:
        # Return generic active for unknown GSTINs (realistic behavior)
        return jsonify({
            'valid': True, 'gstin': gstin, 'status': 'ACTIVE',
            'taxpayer_type': 'Regular', 'state_code': gstin[:2]
        })
    
    response = {
        'valid': True, 'gstin': gstin,
        'legal_name': vendor.get('name'), 'status': vendor['status'],
        'state_code': gstin[:2], 'taxpayer_type': vendor.get('type', 'Regular')
    }
    if vendor['status'] == 'SUSPENDED':
        response['suspension_date'] = vendor.get('suspension_date', '2024-08-01')
        response['suspension_reason'] = 'Non-filing of returns'
    if vendor['status'] == 'CANCELLED':
        response['cancellation_date'] = '2024-05-15'
        response['cancellation_reason'] = 'Voluntary cancellation'
    
    # Simulate slight delay for realism
    time.sleep(random.uniform(0.1, 0.5))
    return jsonify(response)

@app.route('/api/gst/hsn-rate', methods=['GET'])
def get_hsn_rate():
    """Get GST rate for HSN/SAC code based on invoice date."""
    code = request.args.get('code', '').strip()
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Temporal rate mapping (simplified from gst_rates_schedule.csv)
    rates = {
        '995411': [  # Construction services
            {'from': '2017-07-01', 'to': '2019-03-31', 'cgst': 9, 'sgst': 9, 'igst': 18},
            {'from': '2019-04-01', 'to': None, 'cgst': 6, 'sgst': 6, 'igst': 12}
        ],
        '48025510': [  # A4 paper
            {'from': '2017-07-01', 'to': '2022-09-30', 'cgst': 6, 'sgst': 6, 'igst': 12},
            {'from': '2022-10-01', 'to': None, 'cgst': 9, 'sgst': 9, 'igst': 18}
        ]
    }
    
    if code not in rates:
        return jsonify({
            'hsn_sac': code, 'rate': {'cgst': 9, 'sgst': 9, 'igst': 18},
            'effective_from': '2017-07-01', 'notes': 'Default rate'
        })
    
    # Find matching temporal window
    for window in rates[code]:
        from_date = window['from']
        to_date = window['to'] or '2099-12-31'
        if from_date <= date_str <= to_date:
            return jsonify({
                'hsn_sac': code,
                'rate': {'cgst': window['cgst'], 'sgst': window['sgst'], 'igst': window['igst']},
                'effective_from': window['from'],
                'effective_to': window['to'],
                'notes': f"Rate valid from {window['from']}" + (f" to {window['to']}" if window['to'] else "")
            })
    
    return jsonify({'error': 'NO_RATE_FOUND', 'message': f'No rate found for {code} on {date_str}'}), 404

@app.route('/api/tds/check-206ab', methods=['POST'])
def check_206ab():
    """Check if PAN is flagged under Section 206AB (higher TDS for non-filers)."""
    data = request.json or {}
    pan = data.get('pan', '').upper().strip()
    
    # Known 206AB flagged PANs (from test data)
    flagged_pans = ['AXXPK5566Q']
    
    response = {
        'pan': pan,
        'section_206ab_applicable': pan in flagged_pans,
        'verification_date': datetime.now().strftime('%Y-%m-%d')
    }
    if pan in flagged_pans:
        response['reason'] = 'Non-filer of ITR for preceding 2 assessment years'
        response['minimum_rate'] = 5.0
    
    time.sleep(random.uniform(0.1, 0.3))
    return jsonify(response)

@app.route('/api/gst/verify-irn', methods=['POST'])
def verify_irn():
    """Validate e-Invoice IRN."""
    data = request.json or {}
    irn = data.get('irn', '').strip()
    
    if len(irn) < 50:
        return jsonify({'valid': False, 'error': 'IRN_NOT_FOUND'}), 404
    
    return jsonify({
        'valid': True, 'irn': irn, 'status': 'ACTIVE',
        'generation_date': '2024-09-15T10:30:00Z'
    })

if __name__ == '__main__':
    print("🚀 Mock GST API running on http://localhost:8080")
    app.run(port=8080, debug=False, threaded=True)