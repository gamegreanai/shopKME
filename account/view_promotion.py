# views_account.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import PromotionForm, PromotionImageFormSet
from .models import Promotion


def staff_guard(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def staff_required(view):
    return login_required(user_passes_test(staff_guard)(view))


@staff_required
def promotion_list(request):
    """โหมดรายการ"""
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()  # all/active/inactive/upcoming/expired

    qs = Promotion.objects.filter(is_deleted=False).order_by("-priority", "-starts_at", "-id")

    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(short_text__icontains=q) |
            Q(description__icontains=q)
        )

    now = timezone.now()
    if status == "active":
        qs = qs.filter(active=True, starts_at__lte=now).exclude(ends_at__lt=now)
    elif status == "inactive":
        qs = qs.filter(active=False)
    elif status == "upcoming":
        qs = qs.filter(starts_at__gt=now)
    elif status == "expired":
        qs = qs.filter(ends_at__lt=now)

    page_obj = Paginator(qs, 12).get_page(request.GET.get("page"))

    return render(request, "staff/promotion_manage.html", {
        "mode": "list",
        "page_obj": page_obj,
        "q": q,
        "status": status,
    })


@staff_required
@transaction.atomic
def promotion_create(request):
    """โหมดสร้าง"""
    if request.method == "POST":
        form = PromotionForm(request.POST, request.FILES)
        formset = PromotionImageFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            promo = form.save(commit=False)
            promo.created_by = request.user
            promo.save()
            formset.instance = promo
            formset.save()
            messages.success(request, "สร้างโปรโมชันเรียบร้อย")
            return redirect("account:promotion_list")
        messages.error(request, "ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง")
    else:
        form = PromotionForm()
        formset = PromotionImageFormSet()

    return render(request, "staff/promotion_manage.html", {
        "mode": "create",
        "form": form,
        "formset": formset,
    })


@staff_required
@transaction.atomic
def promotion_update(request, pk):
    """โหมดแก้ไข"""
    promo = get_object_or_404(Promotion, pk=pk, is_deleted=False)

    if request.method == "POST":
        form = PromotionForm(request.POST, request.FILES, instance=promo)
        formset = PromotionImageFormSet(request.POST, request.FILES, instance=promo)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "แก้ไขโปรโมชันเรียบร้อย")
            return redirect("account:promotion_list")
        messages.error(request, "ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง")
    else:
        form = PromotionForm(instance=promo)
        formset = PromotionImageFormSet(instance=promo)

    return render(request, "staff/promotion_manage.html", {
        "mode": "edit",
        "form": form,
        "formset": formset,
        "promo": promo,
    })


@staff_required
def promotion_delete(request, pk):
    """โหมดยืนยันลบ (soft delete)"""
    promo = get_object_or_404(Promotion, pk=pk, is_deleted=False)

    if request.method == "POST":
        promo.is_deleted = True
        promo.active = False
        promo.save(update_fields=["is_deleted", "active"])
        messages.success(request, "ลบโปรโมชันแล้ว (soft delete)")
        return redirect("account:promotion_list")

    return render(request, "staff/promotion_manage.html", {
        "mode": "delete",
        "promo": promo,
    })


@staff_required
def promotion_toggle_active(request, pk):
    """สลับเปิด/ปิด"""
    promo = get_object_or_404(Promotion, pk=pk, is_deleted=False)
    promo.active = not promo.active
    promo.save(update_fields=["active"])
    messages.success(request, f"อัปเดตสถานะเป็น {'เปิด' if promo.active else 'ปิด'} แล้ว")
    return redirect("account:promotion_list")
