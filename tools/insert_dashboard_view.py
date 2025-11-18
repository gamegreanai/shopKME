import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
views_file = os.path.join(ROOT, 'account', 'views.py')

with open(views_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the insertion point: after logout_view
insertion_point = content.find('# 🔹 โปรไฟล์ — แก้ไขข้อมูลส่วนตัว')

if insertion_point == -1:
    print("Could not find insertion point")
    exit(1)

# Create the new dashboard_view function
dashboard_view_code = '''# 🔹 แดชบอร์ด - หน้าหลักของผู้ใช้
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

# Insert the new function
new_content = content[:insertion_point] + dashboard_view_code + content[insertion_point:]

with open(views_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✓ Added dashboard_view to views.py")
