from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from account.models import Profile

class ProfileCompletionMiddleware(MiddlewareMixin):
    """
    ตรวจสอบว่า user กรอกข้อมูลโปรไฟล์ครบหรือยัง
    ถ้ายังไม่ครบ จะ redirect ไปที่หน้า /account/profile/
    เฉพาะในบางเส้นทาง เช่น /shop/checkout/
    """

    def process_request(self, request):
        # ✅ ตรวจสอบเฉพาะผู้ใช้ที่ล็อกอินแล้วเท่านั้น
        if request.user.is_authenticated:
            # ✅ กำหนดเส้นทางที่ต้องตรวจสอบความครบของโปรไฟล์
            protected_paths = [
                '/shop/checkout/',
                '/shop/order/',
            ]

            # ✅ ตรวจเฉพาะ URL ที่อยู่ใน protected_paths
            if any(request.path.startswith(p) for p in protected_paths):
                profile = Profile.objects.filter(user=request.user).first()

                # ✅ ตรวจว่ากรอกข้อมูลสำคัญครบหรือไม่
                missing_info = not profile or not profile.first_name or not profile.address
                if missing_info:
                    messages.warning(request, "กรุณากรอกข้อมูลส่วนตัวให้ครบก่อนทำการสั่งซื้อ 📝")
                    return redirect(reverse('profile'))

        # ✅ ผ่านต่อไป (ไม่ redirect)
        return None
