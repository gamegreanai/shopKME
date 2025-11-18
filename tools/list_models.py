import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
datafile = os.path.join(ROOT, 'data.json')
with open(datafile, 'r', encoding='utf-8') as f:
    data = json.load(f)

models = {}
for o in data:
    m = o.get('model')
    models[m] = models.get(m, 0) + 1

for m, c in sorted(models.items()):
    print(f"{m}: {c}")
