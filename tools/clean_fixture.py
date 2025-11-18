import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
infile = os.path.join(ROOT, 'data.json')
outfile = os.path.join(ROOT, 'data_clean.json')

with open(infile, 'r', encoding='utf-8') as f:
    data = json.load(f)

# collect PKs for account.coupon and account.user
coupon_pks = set(o['pk'] for o in data if o.get('model') == 'account.coupon')
user_pks = set(o['pk'] for o in data if o.get('model') == 'account.user')

cleaned = []
removed = []
for o in data:
    if o.get('model') == 'account.couponredemption':
        fields = o.get('fields', {})
        coupon = fields.get('coupon')
        user = fields.get('user')
        if coupon in coupon_pks and user in user_pks:
            cleaned.append(o)
        else:
            removed.append(o)
    else:
        cleaned.append(o)

with open(outfile, 'w', encoding='utf-8') as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print('Wrote', outfile)
print('Removed couponredemption entries:', len(removed))
