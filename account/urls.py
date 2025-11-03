from django.urls import path
from . import views,view_coupon

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('address/', views.address_view, name='address'),
    path('add-points/', views.add_points_view, name='add_points'),
    path('points/', views.manage_points_view, name='manage_points'),
    path('check-phone/', views.check_phone, name='check_phone'),
    path('adminpanel/points/', views.staff_manage_points, name='adminpanel_manage_points'),
    path('staff/points/', views.staff_manage_points_view, name='staff_manage_points'),
    path('redeem/', views.redeem_view, name="redeem"),

    path('coupon/', view_coupon.coupon_staff_view, name='coupon_staff'),

]
