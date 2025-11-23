from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, F
from django.contrib.admin.views.decorators import staff_member_required
from .models import User, Profile,Coupon, CouponRedemption, PointTransaction,Promotion
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
def register_view(request):
    """สมัครสมาชิกด้วยเบอร์โทรศัพท์และรหัสผ่าน แล้วไปหน้า shop"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')

        if not phone or not email or not password:
            return JsonResponse({'status': 'error', 'message': 'กรุณากรอกเบอร์โทรศัพท์ อีเมล และรหัสผ่าน'})

        # ตรวจสอบอีเมลรูปแบบเบื้องต้น
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'status': 'error', 'message': 'รูปแบบอีเมลไม่ถูกต้อง'})

        if User.objects.filter(phone=phone).exists():
            return JsonResponse({'status': 'warning', 'message': 'เบอร์นี้มีอยู่แล้วในระบบ กรุณาเข้าสู่ระบบ'})

        if User.objects.filter(email=email).exists():
            return JsonResponse({'status': 'warning', 'message': 'อีเมลนี้มีอยู่แล้วในระบบ กรุณาเข้าสู่ระบบ'})

        user = User.objects.create(phone=phone, email=email)
        user.set_password(password)
        user.save()

        # ล็อกอินอัตโนมัติ
        user_auth = authenticate(request, phone=phone, password=password)
        if user_auth:
            login(request, user_auth)
            return JsonResponse({
                'status': 'success',
                'message': 'สมัครสมาชิกสำเร็จ!',
                'redirect': '/account/dashboard/'
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
                'redirect': '/account/dashboard/'
            })
        return JsonResponse({'status': 'error', 'message': 'เบอร์โทรศัพท์หรือรหัสผ่านไม่ถูกต้อง'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# 🔹 ลืมรหัสผ่าน / ตั้งรหัสผ่านใหม่
@require_POST
def forgot_password(request):
    phone = (request.POST.get('phone') or '').strip()
    email = (request.POST.get('email') or '').strip()
    password = request.POST.get('password')
    confirm = request.POST.get('confirm_password')

    if not phone or not email or not password or not confirm:
        return JsonResponse({'status': 'error', 'message': 'กรุณากรอกข้อมูลให้ครบถ้วน'})
    if password != confirm:
        return JsonResponse({'status': 'error', 'message': 'รหัสผ่านทั้งสองช่องไม่ตรงกัน'})

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'ไม่พบบัญชีผู้ใช้จากหมายเลขโทรศัพท์นี้'})

    # หากบัญชีมีอีเมลอยู่แล้ว ต้องตรงกัน; ถ้ายังว่าง อัพเดตด้วยอีเมลที่ระบุ
    user_email = (user.email or '').strip()
    if user_email:
        if user_email.lower() != email.lower():
            return JsonResponse({'status': 'error', 'message': 'เบอร์โทรและอีเมลไม่ตรงกับบัญชีนี้'})
    else:
        user.email = email

    # ตั้งรหัสผ่านใหม่
    user.set_password(password)
    user.save()

    # ล็อกอินให้ทันทีถ้าตรวจสอบผ่าน
    user_auth = authenticate(request, phone=phone, password=password)
    if user_auth is not None:
        login(request, user_auth)

    return JsonResponse({'status': 'success', 'message': 'เปลี่ยนรหัสผ่านสำเร็จ', 'redirect': '/account/dashboard/'})


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
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = getattr(user, 'profile', None)

    if request.method == 'POST':
        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        email = (request.POST.get('email') or '').strip()
        points = request.POST.get('points')

        # Address fields from Profile
        title = (request.POST.get('title') or '').strip()
        gender = (request.POST.get('gender') or '').strip()
        house_no = (request.POST.get('house_no') or '').strip()
        moo = (request.POST.get('moo') or '').strip()
        street = (request.POST.get('street') or '').strip()
        subdistrict = (request.POST.get('subdistrict') or '').strip()
        district = (request.POST.get('district') or '').strip()
        province = (request.POST.get('province') or '').strip()
        postal_code = (request.POST.get('postal_code') or '').strip()

        # Basic validation
        if not phone:
            messages.error(request, "กรุณากรอกเบอร์โทรศัพท์")
            return redirect('account:edit_user', user_id=user.id)

        # Update user
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        if email:
            user.email = email
        try:
            user.save()
        except Exception as e:
            messages.error(request, f"บันทึกข้อมูลผู้ใช้ไม่สำเร็จ: {e}")
            return redirect('account:edit_user', user_id=user.id)

        # Ensure profile exists
        if not profile:
            profile = Profile.objects.create(user=user)

        # Convert points
        try:
            pts_val = int(points) if points not in (None, '') else profile.points
        except ValueError:
            messages.error(request, "กรุณาใส่แต้มเป็นตัวเลขเท่านั้น")
            return redirect('account:edit_user', user_id=user.id)

        profile.points = pts_val
        profile.title = title
        profile.gender = gender
        profile.house_no = house_no
        profile.moo = moo
        profile.street = street
        profile.subdistrict = subdistrict
        profile.district = district
        profile.province = province
        profile.postal_code = postal_code
        profile.save()

        messages.success(request, "แก้ไขข้อมูลผู้ใช้สำเร็จ ✅")
        return redirect('account:staff_manage_points')

    return render(request, 'staff/edit_user.html', {
        'user': user,
        'profile': profile,
    })

@staff_member_required
def delete_user(request, user_id):
    """ฟังก์ชันลบผู้ใช้"""
    user = get_object_or_404(User, id=user_id)
    
    try:
        user.delete()
        messages.success(request, f"ลบผู้ใช้ {user.first_name} {user.last_name} สำเร็จ ✅")
    except Exception as e:
        messages.error(request, f"เกิดข้อผิดพลาดในการลบผู้ใช้: {str(e)}")

    return redirect('account:staff_manage_points')

@staff_member_required
def toggle_user_role(request, user_id):
    """เปลี่ยนสิทธิ์ผู้ใช้เป็น staff/admin หรือ user ปกติ"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    user = get_object_or_404(User, id=user_id)
    
    # ป้องกันไม่ให้แก้ไขตัวเอง
    if user.id == request.user.id:
        messages.warning(request, "⚠️ ไม่สามารถแก้ไขสิทธิ์ของตัวเองได้")
        return redirect('account:staff_manage_points')
    
    action = request.POST.get('action')  # 'make_staff', 'make_admin', 'remove_staff'
    
    try:
        if action == 'make_staff':
            user.is_staff = True
            user.is_superuser = False
            user.save()
            messages.success(request, f"✅ เปลี่ยน {user.phone} เป็น Staff สำเร็จ")
        elif action == 'make_admin':
            user.is_staff = True
            user.is_superuser = True
            user.save()
            messages.success(request, f"✅ เปลี่ยน {user.phone} เป็น Admin สำเร็จ")
        elif action == 'remove_staff':
            user.is_staff = False
            user.is_superuser = False
            user.save()
            messages.success(request, f"✅ เปลี่ยน {user.phone} เป็น User ปกติสำเร็จ")
        else:
            messages.error(request, "❌ คำสั่งไม่ถูกต้อง")
    except Exception as e:
        messages.error(request, f"เกิดข้อผิดพลาด: {str(e)}")
    
    return redirect('account:staff_manage_points')

def staff_required(user):
    return user.is_staff or user.is_superuser



@staff_member_required
def staff_manage_points(request):
    """หน้า staff จัดการแต้มผู้ใช้ (เพิ่ม / ลบ / แก้ไข / ลบ user / ดูประวัติ / ค้นหา พร้อมแบ่งหน้า)"""
    query = request.GET.get("q", "")

    # ✅ ดึงรายชื่อผู้ใช้ + ค้นหา
    profiles = Profile.objects.select_related("user").order_by("-points")
    if query:
        profiles = profiles.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__phone__icontains=query)
        )

    # ✅ เพิ่ม/ลดแต้มหลายคน
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_users")
        points_change = request.POST.get("points_change")

        try:
            change = int(points_change)
        except (TypeError, ValueError):
            messages.error(request, "กรุณากรอกจำนวนแต้มให้ถูกต้อง เช่น +100 หรือ -50")
            return redirect("account:staff_manage_points")

        for uid in selected_ids:
            try:
                profile = Profile.objects.get(user_id=uid)
                old_points = profile.points
                profile.points = F("points") + change
                profile.save()
                profile.refresh_from_db()

                # ✅ บันทึกประวัติ
                PointTransaction.objects.create(
                    staff=request.user,
                    user=profile.user,
                    action="add" if change > 0 else "subtract",
                    points=abs(change),
                )

                messages.success(
                    request,
                    f"✅ {profile.user.phone} {change:+} แต้ม (จาก {old_points} → {profile.points})",
                )
            except Profile.DoesNotExist:
                messages.error(request, f"❌ ไม่พบผู้ใช้ ID {uid}")

        return redirect("account:staff_manage_points")

    # ✅ Pagination สำหรับ profiles (รายชื่อผู้ใช้)
    user_paginator = Paginator(profiles, 10)
    user_page_number = request.GET.get("user_page")
    profiles_page = user_paginator.get_page(user_page_number)

    # ✅ Pagination สำหรับ history (ประวัติ log staff)
    history_qs = PointTransaction.objects.select_related("staff", "user").order_by("-created_at")
    history_paginator = Paginator(history_qs, 10)
    history_page_number = request.GET.get("history_page")
    history_page = history_paginator.get_page(history_page_number)

    # ✅ ส่งค่าไป template
    context = {
        "profiles": profiles_page,
        "query": query,
        "history": history_page,
    }
    return render(request, "staff/staff_manage_points.html", context)


# Override dashboard view to show Name/Address form
@login_required
def dashboard_view(request):
    """แสดงฟอร์มให้กรอก ชื่อ-นามสกุล และ ที่อยู่ ของผู้ใช้"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    meter = calc_level(getattr(profile, "points", 0))
    now = timezone.now()
    qs = (
        Promotion.objects
        .filter(active=True, is_deleted=False, starts_at__lte=now)
        .exclude(ends_at__lt=now)
        .prefetch_related("images", "coupon")
        .order_by("-priority", "-starts_at", "-id")
    )
    paginator = Paginator(qs, 6)         
    page = request.GET.get("page") or 1
    promotions_page = paginator.get_page(page)
    cart = getattr(request, "cart", None)
    subtotal = getattr(cart, "subtotal", None)
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
        "promotions": promotions_page,
        "cart": cart,
        "subtotal": subtotal,
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

    # --- GET: แสดงพาร์ทเนอร์และประวัติเท่านั้น ---
    # ไม่แสดงคูปองโดยตรงในหน้านี้อีกต่อไป

    # 🔹 ไม่แสดงคูปองโดยตรง - ลบฟังก์ชั่นนี้แล้ว
    # คูปองจะแสดงผ่านหน้า Partner Detail เท่านั้น

    # 🔹 ประวัติการแลก
    redemptions = (
        CouponRedemption.objects.select_related("coupon")
        .filter(user=request.user)
        .order_by("-created_at")
    )

    # 🔹 คูปองของฉัน (เฉพาะที่ยังไม่หมดอายุ)
    my_coupons = (
        CouponRedemption.objects.select_related("coupon")
        .filter(
            user=request.user, 
            order_id="",
            coupon__ends_at__gte=timezone.now()
        )
        .order_by("-created_at")
    )

    # 🔹 ดึงพาร์ทเนอร์ที่เปิดใช้งานและจัดกลุ่มตามหมวดหมู่
    from .models import Partner
    partners = Partner.objects.filter(is_active=True).order_by('category', 'subcategory', 'name')
    
    # จัดกลุ่มพาร์ทเนอร์
    partners_by_category = {
        'partner': [],
        'ddream_all': [],
        'ddream_special': [],
        'ddream_used': []
    }
    
    # เวลาปัจจุบัน (ใช้ timezone ที่ import ไว้แล้วตอนต้นไฟล์)
    now = timezone.now()
    
    for p in partners:
        if p.category == 'partner':
            partners_by_category['partner'].append(p)
        elif p.category == 'ddream':
            # ตรวจสอบว่าพาร์ทเนอร์มีคูปองที่หมดอายุหรือไม่
            has_expired_coupons = p.coupons.filter(
                is_deleted=False,
                ends_at__lt=now
            ).exists()
            
            # ตรวจสอบว่ามีคูปองที่ยังไม่หมดอายุหรือไม่
            has_active_coupons = p.coupons.filter(
                is_deleted=False,
                ends_at__gte=now
            ).exists()
            
            if p.subcategory == 'special' and has_active_coupons:
                partners_by_category['ddream_special'].append(p)
            elif has_expired_coupons and not has_active_coupons:
                # แสดงในแท็บ "ใช้แล้ว/หมดอายุ" เฉพาะพาร์ทเนอร์ที่คูปองหมดอายุทั้งหมด
                partners_by_category['ddream_used'].append(p)
            elif has_active_coupons:
                # แสดงในแท็บ "ทั้งหมด" เฉพาะพาร์ทเนอร์ที่มีคูปองยังใช้ได้
                partners_by_category['ddream_all'].append(p)
    
    # เรียงคูปองดีดรีม/ทั้งหมด ตามคะแนนน้อยไปมาก
    def get_min_points(partner):
        coupons = partner.coupons.filter(is_deleted=False)
        points_list = [c.required_points for c in coupons if c.required_points is not None]
        min_point = min(points_list) if points_list else 9999999
        print(f"Partner: {partner.name}, Min Points: {min_point}, Points List: {points_list}")  # Debug
        return min_point
    
    partners_by_category['ddream_all'].sort(key=get_min_points)
    print("Sorted DDream Partners:", [p.name for p in partners_by_category['ddream_all']])  # Debug

    # 🔹 ดึงรูปภาพสไลด์คูปอง
    from .models import CouponSlideImage
    slide_images = CouponSlideImage.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    # จัดรูปเป็นคู่ๆ สำหรับ carousel (แสดงทีละ 2 รูป)
    slide_image_list = list(slide_images)
    image_pairs = []
    for i in range(0, len(slide_image_list), 2):
        pair = {
            'first': slide_image_list[i],
            'second': slide_image_list[i+1] if i+1 < len(slide_image_list) else None
        }
        image_pairs.append(pair)

    context = {
        "profile": profile,
        "meter": meter,
        "redemptions": redemptions,
        "my_coupons": my_coupons,
        "partners_by_category": partners_by_category,
        "slide_images": slide_image_list,
        "image_pairs": image_pairs,
        "now": timezone.now()
    }
    return render(request, "account/redeem.html", context)


@login_required
def partner_coupons_api(request, partner_id):
    """API สำหรับดึงคูปองของพาร์ทเนอร์"""
    from .models import Partner
    from django.utils import timezone
    import json
    
    try:
        partner = Partner.objects.get(pk=partner_id, is_active=True)
        # กรองเฉพาะคูปองที่ยังไม่หมดอายุ
        now = timezone.now()
        coupons = partner.coupons.filter(
            is_deleted=False,
            ends_at__gte=now
        ).order_by('-created_at')
        
        profile = request.user.profile if hasattr(request.user, 'profile') else None
        user_points = profile.points if profile else 0
        
        coupon_list = []
        for c in coupons:
            req_pts = getattr(c, 'required_points', 0) or 0
            coupon_list.append({
                'id': c.id,
                'code': c.code,
                'name': c.name,
                'required_points': req_pts,
                'expires_at': c.ends_at.isoformat() if c.ends_at else None,
                'active': c.active,
                'enough_points': user_points >= req_pts,
                'note': c.note or '',
                'image_code_url': c.image_code.url if c.image_code else '',
                'available_branches': partner.available_branches or 'ใช้ได้ทุกสาขา',
            })
        
        # ดึงรูปคูปองสไลด์ที่เชื่อมกับพาร์ทเนอร์นี้
        slide_image_url = ''
        slide_images = partner.slide_images.filter(is_active=True).order_by('sort_order').first()
        if slide_images and slide_images.image:
            slide_image_url = slide_images.image.url
        
        return JsonResponse({
            'success': True,
            'partner_name': partner.name,
            'partner': {
                'id': partner.id,
                'name': partner.name,
                'title': partner.title or '',
                'available_branches': partner.available_branches or 'ใช้ได้ทุกสาขา',
                'slide_image_url': slide_image_url,
            },
            'coupons': coupon_list
        })
    except Partner.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Partner not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@staff_member_required
def coupon_slide_view(request):
    """จัดการรูปภาพคูปองแบบสไลด์"""
    from .models import CouponSlideImage, Partner
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # การแลกคูปอง
        if action == 'redeem':
            profile, _ = Profile.objects.get_or_create(user=request.user)
            cid = request.POST.get('coupon_id')
            coupon = get_object_or_404(Coupon, pk=cid)

            # ตรวจสอบสิทธิ์และแต้ม
            if not coupon.is_active_now():
                messages.error(request, 'คูปองนี้ไม่อยู่ในช่วงใช้งาน')
                return redirect('account:coupon_slide')

            if not coupon.can_user_use(request.user):
                messages.error(request, 'คูปองนี้ไม่ตรงกับระดับสมาชิกของคุณหรือเกินสิทธิ์การใช้ต่อผู้ใช้')
                return redirect('account:coupon_slide')

            req_pts = getattr(coupon, 'required_points', 0) or 0
            if profile.points < req_pts:
                messages.error(request, 'แต้มสะสมไม่เพียงพอสำหรับการแลกคูปองนี้')
                return redirect('account:coupon_slide')

            # บันทึกแบบ atomic
            with transaction.atomic():
                c = Coupon.objects.select_for_update().get(pk=coupon.pk)
                
                if not c.active:
                    messages.error(request, 'คูปองนี้ถูกใช้เต็มจำนวนแล้ว')
                    return redirect('account:coupon_slide')

                # หักแต้ม
                profile.points = F('points') - req_pts
                profile.save(update_fields=['points'])
                profile.refresh_from_db(fields=['points'])

                # บันทึกการแลก
                redemption, created = CouponRedemption.objects.get_or_create(
                    coupon=c,
                    user=request.user,
                    order_id='',
                    defaults={'discount_applied': Decimal('0.00')},
                )
                
                if not created:
                    messages.warning(request, 'คุณได้แลกคูปองนี้ไปแล้ว')
                    return redirect('account:coupon_slide')

                # ปิดคูปอง
                updated = Coupon.objects.filter(pk=c.pk, active=True).update(
                    use_count=F('use_count') + 1,
                    active=False
                )
                if updated == 0:
                    messages.error(request, 'คูปองนี้ถูกใช้เต็มจำนวนแล้ว')
                    return redirect('account:coupon_slide')

            messages.success(request, 'แลกคูปองสำเร็จ ✅')
            return redirect('account:coupon_slide')
        
        elif action == 'add_image':
            name = request.POST.get('image_name', '').strip()
            image_file = request.FILES.get('image_file')
            sort_order = request.POST.get('sort_order', 0)
            partner_id = request.POST.get('partner_id', '').strip()
            
            if name and image_file:
                try:
                    partner = None
                    if partner_id:
                        try:
                            partner = Partner.objects.get(id=partner_id)
                        except Partner.DoesNotExist:
                            pass
                    
                    CouponSlideImage.objects.create(
                        name=name,
                        image=image_file,
                        sort_order=int(sort_order) if sort_order else 0,
                        partner=partner
                    )
                    messages.success(request, f'เพิ่มรูปภาพ "{name}" เรียบร้อยแล้ว')
                except Exception as e:
                    messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            else:
                messages.error(request, 'กรุณากรอกข้อมูลให้ครบถ้วน')
            
            return redirect('account:coupon_slide')
        
        elif action == 'edit':
            image_id = request.POST.get('image_id')
            image_name = request.POST.get('image_name', '').strip()
            sort_order = request.POST.get('sort_order', 0)
            partner_id = request.POST.get('partner_id', '').strip()
            new_image_file = request.FILES.get('new_image_file')  # รูปใหม่ (optional)
            
            if image_id and image_name:
                try:
                    img = CouponSlideImage.objects.get(id=image_id)
                    img.name = image_name
                    img.sort_order = int(sort_order) if sort_order else 0
                    
                    # อัพเดทพาร์ทเนอร์
                    if partner_id:
                        try:
                            img.partner = Partner.objects.get(id=partner_id)
                        except Partner.DoesNotExist:
                            img.partner = None
                    else:
                        img.partner = None
                    
                    # ถ้ามีการอัพโหลดรูปใหม่
                    if new_image_file:
                        # ลบรูปเก่า
                        if img.image:
                            import os
                            try:
                                if os.path.isfile(img.image.path):
                                    os.remove(img.image.path)
                            except Exception as e:
                                print(f"Warning: Could not delete old image file: {e}")
                        
                        # บันทึกรูปใหม่
                        img.image = new_image_file
                        messages.success(request, f'แก้ไขข้อมูลและเปลี่ยนรูปภาพ "{image_name}" เรียบร้อยแล้ว')
                    else:
                        messages.success(request, f'แก้ไขข้อมูลรูปภาพ "{image_name}" เรียบร้อยแล้ว')
                    
                    img.save()
                except CouponSlideImage.DoesNotExist:
                    messages.error(request, 'ไม่พบรูปภาพนี้')
                except Exception as e:
                    messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            
            return redirect('account:coupon_slide')
        
        elif action == 'delete':
            image_id = request.POST.get('image_id')
            
            if image_id:
                try:
                    img = CouponSlideImage.objects.get(id=image_id)
                    img_name = img.name
                    
                    # ลบไฟล์รูปภาพจากระบบ
                    if img.image:
                        import os
                        if os.path.isfile(img.image.path):
                            os.remove(img.image.path)
                    
                    img.delete()
                    messages.success(request, f'ลบรูปภาพ "{img_name}" เรียบร้อยแล้ว')
                except CouponSlideImage.DoesNotExist:
                    messages.error(request, 'ไม่พบรูปภาพนี้')
                except Exception as e:
                    messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            
            return redirect('account:coupon_slide')
        
        elif action == 'change_image':
            image_id = request.POST.get('image_id')
            new_image_file = request.FILES.get('new_image_file')
            
            if image_id and new_image_file:
                try:
                    img = CouponSlideImage.objects.get(id=image_id)
                    
                    # ลบรูปเก่า
                    if img.image:
                        import os
                        try:
                            if os.path.isfile(img.image.path):
                                os.remove(img.image.path)
                        except Exception as e:
                            print(f"Warning: Could not delete old image file: {e}")
                    
                    # บันทึกรูปใหม่
                    img.image = new_image_file
                    img.save()
                    
                    messages.success(request, f'เปลี่ยนรูปภาพ "{img.name}" เรียบร้อยแล้ว')
                except CouponSlideImage.DoesNotExist:
                    messages.error(request, 'ไม่พบรูปภาพนี้')
                except Exception as e:
                    messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            else:
                messages.error(request, 'กรุณาเลือกไฟล์รูปภาพใหม่')
            
            return redirect('account:coupon_slide')
    
    # GET request - เรียงตาม sort_order (ตัวเลขน้อยไปมาก)
    images = list(CouponSlideImage.objects.select_related('partner').all().order_by('sort_order', 'name'))
    
    # ดึงรายการพาร์ทเนอร์ทั้งหมดสำหรับ dropdown
    partners = Partner.objects.filter(is_active=True).order_by('name')
    
    # ดึงข้อมูล profile เพื่อแสดงแต้ม
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    # จัดรูปเป็นคู่ๆ สำหรับ carousel (แสดงทีละ 2 รูป)
    image_pairs = []
    for i in range(0, len(images), 2):
        pair = {
            'first': images[i],
            'second': images[i+1] if i+1 < len(images) else None
        }
        image_pairs.append(pair)
    
    return render(request, 'coupons/coupon_slide.html', {
        'images': images,
        'image_pairs': image_pairs,
        'partners': partners,
        'profile': profile,
    })

