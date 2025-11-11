from django.urls import path
from django.shortcuts import redirect
from . import views, view_coupon,view_promotion

app_name = 'account'

urlpatterns = [
    path('', lambda request: redirect('account:dashboard'), name='account_root'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('address/', views.address_view, name='address'),
    path('add-points/', views.add_points_view, name='add_points'),
    path('points/', views.manage_points_view, name='manage_points'),
    path('check-phone/', views.check_phone, name='check_phone'),

    # ✅ ใช้ view ที่มี pagination ตัวเดียวกันทั้งสองหน้า
    path('adminpanel/points/', views.staff_manage_points, name='adminpanel_manage_points'),
    path('staff/points/', views.staff_manage_points, name='staff_manage_points'),

    path('redeem/', views.redeem_view, name="redeem"),
    path('staff/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('staff/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('coupon/', view_coupon.coupon_staff_view, name='coupon_staff'),

    path('staff/promotion/',               view_promotion.promotion_list,   name='promotion_list'),
    path('staff/promotion/create/',        view_promotion.promotion_create, name='promotion_create'),
    path('staff/promotion/<int:pk>/edit/', view_promotion.promotion_update, name='promotion_edit'),
    path('staff/promotion/<int:pk>/delete/', view_promotion.promotion_delete, name='promotion_delete'),
    path('staff/promotion/<int:pk>/toggle/', view_promotion.promotion_toggle_active, name='promotion_toggle'),
    path('promotion/<int:pk>/', view_promotion.promotion_detail, name='promotion_detail'),
    
]
