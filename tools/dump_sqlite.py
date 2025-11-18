import os
import sys

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopKME.settings_sqlite')
import django
django.setup()

from django.core.management import call_command

output_file = os.path.join(PROJECT_ROOT, 'data.json')
print('Writing fixture to', output_file)
with open(output_file, 'w', encoding='utf-8') as f:
    call_command('dumpdata', exclude=['auth.permission', 'contenttypes', 'admin.logentry'], indent=2, stdout=f)

print('Done')
