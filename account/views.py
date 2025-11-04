from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import F
from django.contrib.admin.views.decorators import staff_member_required

from .models import User, Profile,Coupon, CouponRedemption
from django.db import transaction 
from decimal import Decimal
from .forms import RegisterForm, LoginForm, ProfileForm, AddressForm, CombinedProfileForm,UserForm,ProfileAddressForm

LEVELS = [
    ("Silver", 0,    500),   # [ชื่อ, floor, next_cap)
    ("Gold",   500, 1000),
    ("Premium",1000, None),   # None = ขั้นสูงสุด
]

def calc_level(points: int):
    p = max(int(points or 0), 0)
    for name, floor, cap in LEVELS:
        if cap is None or p < cap:
            # ความคืบหน้าภายในเลเวลปัจจุบัน
            if cap is None:
                progress = 100
                next_name, remain = None, 0
            else:
                progress = int(((p - floor) / (cap - floor)) * 100) if p >= floor else 0
                next_name = "Premium" if name == "Gold" else "Gold"
                remain = max(cap - p, 0)
            return {
                "level": name,
                "points": p,
                "progress_pct": max(0, min(progress, 100)),
                "next_level_name": next_name,
                "remain_to_next": remain,
            }
    # กันพลาด
    return {"level": "Silver", "points": p, "progress_pct": 0, "next_level_name": "Gold", "remain_to_next": max(1000-p,0)}

# 🔹 สมัครสมาชิก
@csrf_exempt
def register_view(request):
    """สมัครสมาชิกด้วยเบอร์โทรศัพท์และรหัสผ่าน แล้วไปหน้า shop"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        if not phone or not password:
            return JsonResponse({'status': 'error', 'message': 'กรุณากรอกเบอร์โทรศัพท์และรหัสผ่าน'})

        if User.objects.filter(phone=phone).exists():
            return JsonResponse({'status': 'warning', 'message': 'เบอร์นี้มีอยู่แล้วในระบบ กรุณาเข้าสู่ระบบ'})

        user = User.objects.create(phone=phone)
        user.set_password(password)
        user.save()

        # ล็อกอินอัตโนมัติ
        user_auth = authenticate(request, phone=phone, password=password)
        if user_auth:
            login(request, user_auth)
            return JsonResponse({
                'status': 'success',
                'message': 'สมัครสมาชิกสำเร็จ!',
                'redirect': 'account/dashboard/'
            })

        return JsonResponse({'status': 'error', 'message': 'เกิดข้อผิดพลาดในการเข้าสู่ระบบ'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# 🔹 เข้าสู่ระบบ
@csrf_exempt
def login_view(request):
    """เข้าสู่ระบบด้วยเบอร์โทรศัพท์และรหัสผ่าน แล้วไปหน้า shop"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        user = authenticate(request, phone=phone, password=password)
        if user:
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'message': 'เข้าสู่ระบบสำเร็จ!',
                'redirect': 'account/dashboard/'
            })
        return JsonResponse({'status': 'error', 'message': 'เบอร์โทรศัพท์หรือรหัสผ่านไม่ถูกต้อง'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# 🔹 ออกจากระบบ
def logout_view(request):
    logout(request)
    return redirect('/')



# 🔹 โปรไฟล์ — แก้ไขข้อมูลส่วนตัว
@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        uform = UserForm(request.POST, instance=request.user)
        pform = ProfileForm(request.POST, instance=profile)

        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            messages.success(request, "บันทึกข้อมูลสำเร็จแล้ว ✅")
            return redirect("account:profile")
        else:
            messages.error(request, "กรุณาตรวจสอบข้อมูลที่กรอก")
    else:
        uform = UserForm(instance=request.user)
        pform = ProfileForm(instance=profile)
    return render(
        request,
        "account/profile_form.html",
        {"uform": uform, "pform": pform, "profile": profile},
    )


# 🔹 ที่อยู่ — เพิ่ม / แก้ไข / ลบ
@login_required
def address_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileAddressForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "บันทึกที่อยู่เรียบร้อยแล้ว ✅")
            return redirect("account:address")  # ตั้งให้ชี้ชื่อ urlpattern ของหน้านี้
        else:
            messages.error(request, "กรุณาตรวจสอบข้อมูลที่กรอก")
    else:
        form = ProfileAddressForm(instance=profile)

    return render(request, "account/address_form.html", {"form": form, "profile": profile})


# 🔹 หน้าแลกพอยต์ (Redeem)
from django.utils import timezone


# 🔹 แอดมิน: เพิ่มหรือลบพอยต์ให้ผู้ใช้
@staff_member_required
def add_points_view(request):
    users = Profile.objects.select_related('user')
    if request.method == 'POST':
        phone = request.POST.get('phone')
        change = request.POST.get('points', '')

        try:
            change_value = int(change)
        except ValueError:
            messages.error(request, "กรุณาใส่จำนวนพอยต์เป็นตัวเลข เช่น +500 หรือ -200")
            return redirect('add_points')

        try:
            profile = Profile.objects.get(user__phone=phone)
            profile.points = F('points') + change_value
            profile.save()
            messages.success(request, f"อัปเดตพอยต์ของ {phone} เรียบร้อยแล้ว ✅")
        except Profile.DoesNotExist:
            messages.error(request, "ไม่พบบัญชีนี้ในระบบ")

        return redirect('add_points')

    return render(request, 'account/add_points.html', {'users': users})


# 🔹 ตรวจสอบเบอร์โทร
@require_GET
def check_phone(request):
    phone = request.GET.get('phone')
    if not phone:
        return JsonResponse({'exists': False, 'message': 'กรุณาระบุหมายเลขโทรศัพท์'})
    exists = User.objects.filter(phone=phone).exists()
    if exists:
        return JsonResponse({'exists': True, 'message': 'เบอร์นี้มีอยู่ในระบบแล้ว'})
    return JsonResponse({'exists': False, 'message': 'สามารถใช้เบอร์นี้ได้'})


# 🔹 หน้าจัดการแต้ม (สำหรับแอดมิน)
@staff_member_required
def manage_points_view(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    profiles = Profile.objects.select_related('user').all()

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        points_input = request.POST.get("points")

        try:
            points_value = int(points_input)
        except ValueError:
            messages.error(request, "กรุณาใส่ตัวเลขเท่านั้น ❌")
            return redirect("manage_points")

        profile = Profile.objects.get(user_id=user_id)
        profile.points = F('points') + points_value
        profile.save()
        profile.refresh_from_db()

        action = "เพิ่ม" if points_value > 0 else "ลด"
        messages.success(request, f"{action}แต้ม {abs(points_value)} ให้ {profile.user.phone} สำเร็จ ✅")
        return redirect("manage_points")

    return render(request, "account/manage_points.html", {"profiles": profiles})

@staff_member_required
def staff_manage_points(request):
    """หน้า staff สำหรับเพิ่ม/ลดแต้มของผู้ใช้"""
    profiles = Profile.objects.select_related('user').all().order_by('-points')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        points_change = request.POST.get('points_change')

        try:
            points_change = int(points_change)
        except (ValueError, TypeError):
            messages.error(request, "กรุณากรอกจำนวนแต้มเป็นตัวเลข เช่น +100 หรือ -50")
            return redirect('account:staff_manage_points')

        try:
            profile = Profile.objects.get(user_id=user_id)
            profile.points = F('points') + points_change
            profile.save()
            messages.success(request, f"อัปเดตแต้มให้ {profile.user.phone} สำเร็จ ({points_change:+}) ✅")
        except Profile.DoesNotExist:
            messages.error(request, "ไม่พบผู้ใช้นี้")

        return redirect('account:staff_manage_points')

    context = {'profiles': profiles}
    return render(request, 'staff/manage_points.html', context)

@staff_member_required
def staff_dashboard_home(request):
    """
    หน้าแรกของแดชบอร์ดเจ้าหน้าที่
    """
    return render(request, 'staff/staff_dashboard_home.html')



@staff_member_required
def staff_manage_points_view(request):
    """จัดการแต้มของผู้ใช้"""
    profiles = Profile.objects.select_related('user').all()

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")
        points = int(request.POST.get("points", 0))
        profile = Profile.objects.filter(user_id=user_id).first()

        if profile:
            if action == "add":
                profile.points += points
                messages.success(request, f"เพิ่ม {points} แต้มให้ {profile.user.phone} แล้ว ✅")
            elif action == "subtract":
                profile.points = max(0, profile.points - points)
                messages.warning(request, f"ลบ {points} แต้มจาก {profile.user.phone} แล้ว ⚠️")
            profile.save()

        return redirect("account:staff_manage_points")

    return render(request, "staff/staff_manage_points.html", {"profiles": profiles})


# Override dashboard view to show Name/Address form
@login_required
def dashboard_view(request):
    """แสดงฟอร์มให้กรอก ชื่อ-นามสกุล และ ที่อยู่ ของผู้ใช้"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    meter = calc_level(getattr(profile, "points", 0))
    if request.method == 'POST':
        form = CombinedProfileForm(request.POST)
        if form.is_valid():
            form.save(user=request.user, profile=profile)
            messages.success(request, 'บันทึกข้อมูลแล้ว')
            return redirect('account:dashboard')
        else:
            messages.error(request, 'กรุณาตรวจกรอกข้อมูลให้ครบถ้วน')
    else:
        form = CombinedProfileForm(user=request.user, profile=profile)

    return render(request, 'account/dashboard.html', {
        'form': form,
        'profile': profile,
        'meter': meter,
    })
@login_required
def redeem_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    meter = calc_level(getattr(profile, "points", 0))

    # --- POST: redeem ---
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "redeem":
            cid = request.POST.get("coupon_id")
            coupon = get_object_or_404(Coupon, pk=cid)

            # 🔹 ตรวจสอบสิทธิ์และแต้ม
            if not coupon.is_active_now():
                messages.error(request, "คูปองนี้ไม่อยู่ในช่วงใช้งาน")
                return redirect("account:redeem")

            if not coupon.can_user_use(request.user):
                messages.error(request, "คูปองนี้ไม่ตรงกับระดับสมาชิกของคุณหรือเกินสิทธิ์การใช้ต่อผู้ใช้")
                return redirect("account:redeem")

            req_pts = getattr(coupon, "required_points", 0) or 0
            if profile.points < req_pts:
                messages.error(request, "แต้มสะสมไม่เพียงพอสำหรับการแลกคูปองนี้")
                return redirect("account:redeem")

            # 🔸 บันทึกแบบ atomic ป้องกันแข่งกันแลก
            with transaction.atomic():
                # ดึงคูปองแบบ lock
                c = Coupon.objects.select_for_update().get(pk=coupon.pk)

                # ถ้าคูปองหมดหรือปิดอยู่แล้ว
                if not c.active:
                    messages.error(request, "คูปองนี้ถูกใช้เต็มจำนวนแล้ว")
                    return redirect("account:redeem")

                # 🔹 หักแต้มจากโปรไฟล์
                profile.points = F("points") - req_pts
                profile.save(update_fields=["points"])
                profile.refresh_from_db(fields=["points"])

                # 🔹 บันทึกการแลก (กันซ้ำด้วย get_or_create)
                redemption, created = CouponRedemption.objects.get_or_create(
                    coupon=c,
                    user=request.user,
                    order_id="",  # ไม่มีออเดอร์
                    defaults={"discount_applied": Decimal("0.00")},
                )

                if not created:
                    messages.warning(request, "คุณได้แลกคูปองนี้ไปแล้ว")
                    return redirect("account:redeem")

                # 🔹 ปิดคูปองหลังแลกครั้งเดียว
                updated = Coupon.objects.filter(pk=c.pk, active=True).update(
                    use_count=F("use_count") + 1,
                    active=False
                )
                if updated == 0:
                    messages.error(request, "คูปองนี้ถูกใช้เต็มจำนวนแล้ว")
                    return redirect("account:redeem")

            messages.success(request, "แลกคูปองสำเร็จ ✅")
            return redirect("account:redeem")

        messages.error(request, "คำสั่งไม่ถูกต้อง")
        return redirect("account:redeem")

    # --- GET: แสดงรายการคูปองที่แลกได้ + ประวัติ ---
    now = timezone.now()
    coupons_qs = (
        Coupon.objects.filter(starts_at__lte=now)
        .exclude(ends_at__lt=now)
        .order_by("ends_at", "code")
    )

    # 🔹 ฟิลเตอร์ให้เหลือเฉพาะ “แลกได้”
    available = []
    for c in coupons_qs:
        req_pts = getattr(c, "required_points", 0) or 0
        can_use = c.can_user_use(request.user)
        enough_points = profile.points >= req_pts

        # เพิ่มข้อมูลช่วยแสดงผลใน template
        c.req_pts = req_pts
        c.enough_points = enough_points
        c.can_use = can_use
        c.expires_at = c.ends_at
        c.percent_off = round(req_pts / 10)
        c.active = c.active
        available.append(c)

    # 🔹 ประวัติการแลก
    redemptions = (
        CouponRedemption.objects.select_related("coupon")
        .filter(user=request.user)
        .order_by("-created_at")
    )

    my_coupons = (
        CouponRedemption.objects.select_related("coupon")
        .filter(user=request.user, order_id="")
        .order_by("-created_at")
    )

    context = {
        "profile": profile,
        "meter": meter,
        "available": available,
        "redemptions": redemptions,
        "my_coupons": my_coupons,
    }
    return render(request, "account/redeem.html", context)

