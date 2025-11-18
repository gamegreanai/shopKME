import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT,'data.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

has23 = any(o.get('model')=='account.coupon' and o.get('pk')==23 for o in data)
print('coupon pk 23 present in data.json:', has23)
count_coupons = sum(1 for o in data if o.get('model')=='account.coupon')
print('total coupons in fixture:', count_coupons)
