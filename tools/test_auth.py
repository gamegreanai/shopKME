import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopKME.settings')
sys.path.insert(0, r'c:\Users\game1\Desktop\shopKME')
django.setup()

from account.models import User
from django.contrib.auth import authenticate

# Test user
phone = '0879512117'

# Check if user exists
user = User.objects.filter(phone=phone).first()
if user:
    print(f"✓ User found: {user.phone}")
    print(f"  First Name: {user.first_name}")
    print(f"  Last Name: {user.last_name}")
    print(f"  Password hash (first 20 chars): {user.password[:20]}")
    
    # Try to authenticate with common passwords
    test_passwords = ['0879512117', 'password', '123456', 'admin', '']
    
    print(f"\nTesting authentication with various passwords:")
    for pwd in test_passwords:
        result = authenticate(phone=phone, password=pwd)
        print(f"  Password '{pwd}': {result}")
else:
    print(f"✗ User with phone {phone} not found")
    print(f"\nAll users in database:")
    for u in User.objects.all():
        print(f"  {u.id}: {u.phone}")
