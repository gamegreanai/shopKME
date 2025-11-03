# views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime
from .models import Coupon, MembershipLevel

MAX_IMAGE_MB = 2

def _parse_dt_local(s: str):
    if not s: return None
    dt = datetime.strptime(s, "%Y-%m-%dT%H:%M")
    return timezone.make_aware(dt, timezone.get_current_timezone())

def _ensure_unique_code(code: str) -> str:
    base = code.strip()
    if not Coupon.objects.filter(code=base).exists(): return base
    i = 2
    while Coupon.objects.filter(code=f"{base}-{i}").exists():
        i += 1
    return f"{base}-{i}"

def _validate_image(file) -> bool:
    if not file: return True
    if not getattr(file, "content_type", "").startswith("image/"):
        return False
    if file.size > MAX_IMAGE_MB * 1024 * 1024:
        return False
    return True

@login_required
@user_passes_test(lambda u: u.is_staff)
def coupon_staff_view(request):
    if request.method == "POST":
        action = request.POST.get("action", "").strip()

        # ---------- CREATE ----------
        if action == "create":
            name = (request.POST.get("name") or "").strip()
            code = (request.POST.get("code") or "").strip()
            required_points = request.POST.get("required_points") or "0"
            ends_at = _parse_dt_local(request.POST.get("expires_at") or "")
            description = (request.POST.get("description") or "").strip()
            img = request.FILES.get("image")

            if not name:
                messages.error(request, "กรุณาระบุชื่อคูปอง")
                return redirect("account:coupon_staff")
            if not _validate_image(img):
                messages.error(request, f"รูปไม่ถูกต้อง (ชนิดไฟล์ต้องเป็นภาพ และไม่เกิน {MAX_IMAGE_MB}MB)")
                return redirect("account:coupon_staff")

            code = _ensure_unique_code(code)
            c = Coupon(
                code=code,
                discount_type=Coupon.FIXED,
                discount_value=0,
                min_spend=0,
                starts_at=timezone.now(),
                ends_at=ends_at,
                active=True,
                note=description,
                allowed_levels=[MembershipLevel.SILVER, MembershipLevel.GOLD, MembershipLevel.PREMIUM],
            )
            try:
                if hasattr(Coupon, "required_points"):
                    c.required_points = int(required_points)
                else:
                    c.note = (f"[points:{int(required_points)}] " + (c.note or "")).strip()
            except ValueError:
                messages.error(request, "แต้มที่ต้องใช้ต้องเป็นตัวเลข")
                return redirect("account:coupon_staff")

            try:
                c.full_clean()
                if img: c.image = img
                c.save()
                messages.success(request, "บันทึกคูปองใหม่เรียบร้อย ✅")
            except Exception as e:
                messages.error(request, f"บันทึกไม่สำเร็จ: {e}")
            return redirect("account:coupon_staff")

        # ---------- TOGGLE ----------
        elif action == "toggle":
            cid = request.POST.get("coupon_id")
            coupon = get_object_or_404(Coupon, pk=cid)
            coupon.active = not coupon.active
            coupon.save(update_fields=["active"])
            messages.success(request, "สลับสถานะคูปองเรียบร้อย ✅")
            return redirect("account:coupon_staff")

        # ---------- SET IMAGE ----------
        elif action == "set_image":
            cid = request.POST.get("coupon_id")
            coupon = get_object_or_404(Coupon, pk=cid)
            img = request.FILES.get("image")
            if not _validate_image(img):
                messages.error(request, f"รูปไม่ถูกต้อง (ชนิดไฟล์ต้องเป็นภาพ และไม่เกิน {MAX_IMAGE_MB}MB)")
                return redirect("account:coupon_staff")
            # ลบไฟล์เก่า (ถ้ามี) แล้วอัปใหม่
            if coupon.image:
                coupon.image.delete(save=False)
            coupon.image = img
            coupon.save(update_fields=["image"])
            messages.success(request, "อัปเดตรูปคูปองเรียบร้อย ✅")
            return redirect("account:coupon_staff")

        # ---------- DELETE IMAGE ----------
        elif action == "delete_image":
            cid = request.POST.get("coupon_id")
            coupon = get_object_or_404(Coupon, pk=cid)
            if coupon.image:
                coupon.image.delete(save=False)
                coupon.image = None
                coupon.save(update_fields=["image"])
            messages.success(request, "ลบรูปคูปองเรียบร้อย ✅")
            return redirect("account:coupon_staff")

        else:
            messages.error(request, "รูปแบบคำสั่งไม่ถูกต้อง")
            return redirect("account:coupon_staff")

    # GET
    coupons = list(Coupon.objects.all().order_by("-created_at"))
    for c in coupons:
        c.expires_at = c.ends_at
        c.is_active = c.active
    return render(request, "coupons/coupon_staff.html", {"coupons": coupons})
