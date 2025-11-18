import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fixture_file = os.path.join(ROOT, 'data_clean.json')
media_root = os.path.join(ROOT, 'media')
report_file = os.path.join(ROOT, 'media_scan_report.txt')

with open(fixture_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract all image/file paths from fixture
media_files = set()
for obj in data:
    fields = obj.get('fields', {})
    for key, value in fields.items():
        if isinstance(value, str) and (
            value.startswith('promotions/') or 
            value.startswith('coupons/') or 
            value.startswith('coupons_qr/')
        ):
            media_files.add(value)

# Check which files exist and which are missing
existing = []
missing = []
total_size = 0

for fpath in sorted(media_files):
    full_path = os.path.join(media_root, fpath)
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        total_size += size
        existing.append((fpath, size))
    else:
        missing.append(fpath)

# Write report
with open(report_file, 'w', encoding='utf-8') as f:
    f.write('=== Media Files Scan Report ===\n')
    f.write(f'Scan Date: {__import__("datetime").datetime.now().isoformat()}\n\n')
    
    f.write(f'Total files referenced in DB: {len(media_files)}\n')
    f.write(f'Files that exist: {len(existing)}\n')
    f.write(f'Files missing: {len(missing)}\n')
    f.write(f'Total size of existing files: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)\n\n')
    
    if existing:
        f.write('=== EXISTING FILES ===\n')
        for fpath, size in existing:
            f.write(f'{fpath}\t{size:,} bytes\n')
        f.write('\n')
    
    if missing:
        f.write('=== MISSING FILES ===\n')
        for fpath in missing:
            f.write(f'{fpath}\n')
        f.write('\n')
    
    f.write('=== End Report ===\n')

print(f'Total files referenced: {len(media_files)}')
print(f'Existing: {len(existing)}, Missing: {len(missing)}')
print(f'Total size: {total_size/1024/1024:.2f} MB')
print(f'Report written to: {report_file}')

# Also write just the file list to media_files_list.txt
with open(os.path.join(ROOT, 'media_files_list.txt'), 'w', encoding='utf-8') as f:
    for fpath in sorted(media_files):
        f.write(fpath + '\n')
print(f'File list written to: media_files_list.txt')
