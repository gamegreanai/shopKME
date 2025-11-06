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
            image_qr = request.FILES.get("image_qr")

            if not name:
                messages.error(request, "กรุณาระบุชื่อคูปอง")
                return redirect("account:coupon_staff")
            if not _validate_image(img):
                messages.error(request, f"รูปไม่ถูกต้อง (ชนิดไฟล์ต้องเป็นภาพ และไม่เกิน {MAX_IMAGE_MB}MB)")
                return redirect("account:coupon_staff")

            code = _ensure_unique_code(code)
            c = Coupon(
                name=name,
                code=code,
                discount_type=Coupon.FIXED,
                discount_value=0,
                min_spend=0,
                starts_at=timezone.now(),
                ends_at=ends_at,
                active=True,
                note=description,
                allowed_levels=[
                    MembershipLevel.SILVER,
                    MembershipLevel.GOLD,
                    MembershipLevel.PREMIUM,
                ],
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
                if img:
                    c.image = img
                if image_qr:
                    c.image_code = image_qr
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
            image_qr = request.FILES.get("image_qr")
            
            if not _validate_image(img):
                messages.error(request, f"รูปไม่ถูกต้อง (ชนิดไฟล์ต้องเป็นภาพ และไม่เกิน {MAX_IMAGE_MB}MB)")
                return redirect("account:coupon_staff")
            if not _validate_image(image_qr):
                messages.error(request, f"รูปไม่ถูกต้อง (ชนิดไฟล์ต้องเป็นภาพ และไม่เกิน {MAX_IMAGE_MB}MB)")
                return redirect("account:coupon_staff")
            # ลบไฟล์เก่า (ถ้ามี) แล้วอัปใหม่
            if coupon.image and img:
                coupon.image.delete(save=False)
                coupon.image = img
                coupon.save(update_fields=["image"])
            if coupon.image_code and image_qr:
                coupon.image_code.delete(save=False)
                coupon.image_code = image_qr
                coupon.save(update_fields=["image_code"])
            
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
        
        # ---------- DELETE COUPON ----------
        elif action == "delete":
            cid = request.POST.get("coupon_id")
            coupon = get_object_or_404(Coupon, pk=cid)
            updated = Coupon.objects.filter(pk=cid).update(is_deleted=True)
            coupon_name = coupon.name
            # ✅ ลบรูปใน storage ก่อน (ถ้ามี)
            # if coupon.image:
            #     coupon.image.delete(save=False)

            # # ✅ ลบคูปองออกจากฐานข้อมูล
            # coupon_name = coupon.name
            # coupon.delete()

            messages.success(request, f"ลบคูปอง '{coupon_name}' เรียบร้อย ✅")
            return redirect("account:coupon_staff")
        # ---------- UPDATE ----------
        elif action == "update":
            cid = request.POST.get("coupon_id")
            c = get_object_or_404(Coupon, pk=cid)
            c.name = request.POST.get("name", c.name).strip()
            c.code = request.POST.get("code", c.code).strip()
            rp = request.POST.get("required_points", "")
            c.required_points = int(rp) if rp != "" else None
            c.note = request.POST.get("description", c.note)

            exp = request.POST.get("expires_at")
            if exp is not None:
                c.ends_at = exp if exp != "" else None

            # จัดการรูป
            if request.POST.get("remove_image") == '1':
                if c.image:
                    c.image.delete(save=False)
                c.image = None
            elif request.FILES.get("image"):
                c.image = request.FILES["image"]
            if request.POST.get("remove_image_code")  == '1':
                if c.image_code:
                    c.image_code.delete(save=False)
                c.image_code = None
            elif request.FILES.get("image_code"):
                c.image_code = request.FILES["image_code"]

            c.save()
            return redirect(request.path)
        
        else:
            messages.error(request, "รูปแบบคำสั่งไม่ถูกต้อง")
            return redirect("account:coupon_staff")

    # ---------- GET ----------
    coupons = list(Coupon.objects.filter(is_deleted = False).order_by("-created_at"))
    now = timezone.now()  # ✅ เพิ่มตัวแปรเวลาสำหรับ template

    for c in coupons:
        c.expires_at = c.ends_at
        c.is_active = c.active
        # ✅ เพิ่มฟิลด์ช่วยแสดงผลใน template
        c.is_expired = c.ends_at and c.ends_at < now
        c.is_fully_used = c.max_uses and c.use_count >= c.max_uses
    return render(
        request,
        "coupons/coupon_staff.html",
        {"coupons": coupons, "now": now},
    )
