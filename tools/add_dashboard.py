#!/usr/bin/env python
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
views_path = os.path.join(root, 'account', 'views.py')

with open(views_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find line number where "# 🔹 โปรไฟล์ — แก้ไขข้อมูลส่วนตัว" appears
insert_at = None
for i, line in enumerate(lines):
    if '# 🔹 โปรไฟล์ — แก้ไขข้อมูลส่วนตัว' in line:
        insert_at = i
        break

if insert_at is None:
    print("ERROR: Could not find insertion point")
    exit(1)

# The new dashboard_view function
dashboard_code = '''# 🔹 แดชบอร์ด - หน้าหลักของผู้ใช้
@login_required
def dashboard_view(request):
    """หน้า dashboard หลักสำหรับผู้ใช้ที่ล็อกอินแล้ว"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    meter = calc_level(profile.points)
    
    # ดึงโปรโมชั่นที่ active ทั้งหมด
    promotions = Promotion.objects.filter(
        active=True,
        is_deleted=False,
        starts_at__lte=timezone.now()
    ).exclude(
        ends_at__lt=timezone.now()
    ).order_by('-priority', '-starts_at')
    
    context = {
        'profile': profile,
        'meter': meter,
        'promotions': promotions,
    }
    return render(request, 'account/dashboard.html', context)

'''

# Insert the code at the correct line
lines.insert(insert_at, dashboard_code)

# Write back
with open(views_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✓ Successfully inserted dashboard_view into views.py")
