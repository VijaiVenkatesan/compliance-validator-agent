import json
from pathlib import Path

# 1. Load results with explicit UTF-8 to handle special characters
results_path = Path('results.json')
with results_path.open('r', encoding='utf-8') as f:
    results = json.load(f)

Path('reports').mkdir(exist_ok=True)

for decision in ['APPROVED', 'REJECTED', 'ESCALATE_TO_HUMAN']:
    sample = next((r for r in results if r.get('overall_decision') == decision), None)
    if sample:
        output_file = Path(f'reports/sample_{decision}.json')
        # 2. Write with UTF-8 and ensure_ascii=False to preserve symbols like ✓ cleanly
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(sample, f, indent=2, ensure_ascii=False)
        print(f'✅ Created {output_file}')
    else:
        print(f'⚠️ No sample found for {decision}')

print('✅ reports/ folder ready for submission')