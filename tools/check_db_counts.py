import os, sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopKME.settings')
import django
django.setup()
from django.apps import apps

models = apps.get_models()
counts = {}
for m in models:
    try:
        counts[f"{m._meta.app_label}.{m._meta.model_name}"] = m.objects.count()
    except Exception as e:
        counts[f"{m._meta.app_label}.{m._meta.model_name}"] = f"error: {e}"

for k in sorted(counts.keys()):
    print(f"{k}: {counts[k]}")
