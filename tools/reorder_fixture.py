import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
infile = os.path.join(ROOT, 'data.json')
outfile = os.path.join(ROOT, 'data_ordered.json')

with open(infile, 'r', encoding='utf-8') as f:
    data = json.load(f)

coupons = [o for o in data if o.get('model') == 'account.coupon']
others = [o for o in data if o.get('model') != 'account.coupon']

# Find first couponredemption in others
first_red_index = None
for i, o in enumerate(others):
    if o.get('model') == 'account.couponredemption':
        first_red_index = i
        break

if first_red_index is None:
    newdata = coupons + others
else:
    newdata = others[:first_red_index] + coupons + others[first_red_index:]

with open(outfile, 'w', encoding='utf-8') as f:
    json.dump(newdata, f, ensure_ascii=False, indent=2)

print('Wrote', outfile)
