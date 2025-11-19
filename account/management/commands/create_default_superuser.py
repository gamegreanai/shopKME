from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates a superuser if it does not exist'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = '0123456789'
        email = 'adminddream1@ddreamclinic.com'
        password = 'Admin5421'
        
        try:
            user = User.objects.get(username=username)
            # ถ้ามี user อยู่แล้ว อัปเดตรหัสผ่าน
            user.set_password(password)
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" updated successfully!'))
            self.stdout.write(self.style.SUCCESS(f'Username: {username}'))
            self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
        except User.DoesNotExist:
            # ถ้ายังไม่มี user สร้างใหม่
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully!'))
            self.stdout.write(self.style.SUCCESS(f'Username: {username}'))
            self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
