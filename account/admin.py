from django.contrib import admin
from .models import User, Profile, Coupon, CouponRedemption, Partner, PointTransaction, Promotion, PromotionImage, PromotionTracking, CouponSlideImage

# Register your models here.

@admin.register(CouponSlideImage)
class CouponSlideImageAdmin(admin.ModelAdmin):
    list_display = ['name', 'image', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    list_editable = ['is_active']
