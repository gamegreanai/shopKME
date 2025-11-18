import os, sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopKME.settings')
import django
django.setup()
from django.core.management import call_command
out = os.path.join(PROJECT_ROOT, 'postgres_backup.json')
with open(out, 'w', encoding='utf-8') as f:
    call_command('dumpdata', indent=2, stdout=f)
print('Wrote', out)
