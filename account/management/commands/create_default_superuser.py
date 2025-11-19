from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates a superuser if it does not exist'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # อ่านค่าจาก Environment Variables (ปลอดภัยกว่า)
        phone = os.getenv('ADMIN_PHONE', '0123456789')
        email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        password = os.getenv('ADMIN_PASSWORD')
        
        # ตรวจสอบว่ามีการตั้งค่ารหัสผ่านหรือไม่
        if not password:
            self.stdout.write(self.style.ERROR('ADMIN_PASSWORD environment variable is not set!'))
            self.stdout.write(self.style.WARNING('Skipping superuser creation for security reasons.'))
            return
        
        try:
            user = User.objects.get(phone=phone)
            # ถ้ามี user อยู่แล้ว อัปเดตรหัสผ่าน
            user.set_password(password)
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser "{phone}" updated successfully!'))
            self.stdout.write(self.style.SUCCESS(f'Phone: {phone}'))
            self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
        except User.DoesNotExist:
            # ถ้ายังไม่มี user สร้างใหม่
            user = User(
                phone=phone,
                email=email,
                is_staff=True,
                is_superuser=True
            )
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser "{phone}" created successfully!'))
            self.stdout.write(self.style.SUCCESS(f'Phone: {phone}'))
            self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
