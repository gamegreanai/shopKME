import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
infile = os.path.join(ROOT, 'data.json')
outfile = os.path.join(ROOT, 'data_no_couponredemption.json')

with open(infile, 'r', encoding='utf-8') as f:
    data = json.load(f)

filtered = [o for o in data if o.get('model') != 'account.couponredemption']

with open(outfile, 'w', encoding='utf-8') as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print('Wrote', outfile, '- removed account.couponredemption entries')
