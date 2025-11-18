"""
สคริปต์แก้ไขข้อมูล foreign key ที่เสียหายใน database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopKME.settings')
django.setup()

from django.db import connection

def fix_invalid_foreign_keys():
    """ลบ CouponRedemption records ที่มี foreign key ไม่ถูกต้อง"""
    with connection.cursor() as cursor:
        # หา CouponRedemption ที่อ้างถึง Coupon ที่ไม่มีอยู่
        cursor.execute("""
            SELECT cr.id, cr.coupon_id 
            FROM account_couponredemption cr
            LEFT JOIN account_coupon c ON cr.coupon_id = c.id
            WHERE c.id IS NULL
        """)
        
        invalid_records = cursor.fetchall()
        
        if invalid_records:
            print(f"พบ {len(invalid_records)} records ที่มี foreign key ไม่ถูกต้อง:")
            for record in invalid_records:
                print(f"  - CouponRedemption ID: {record[0]}, coupon_id: {record[1]} (ไม่มีใน account_coupon)")
            
            # ลบ records ที่เสียหาย
            invalid_ids = [str(record[0]) for record in invalid_records]
            cursor.execute(f"""
                DELETE FROM account_couponredemption 
                WHERE id IN ({','.join(invalid_ids)})
            """)
            
            print(f"\n✅ ลบ {len(invalid_records)} records ที่เสียหายเรียบร้อยแล้ว")
        else:
            print("✅ ไม่พบข้อมูลที่เสียหาย - database สะอาดแล้ว")

if __name__ == '__main__':
    print("🔧 กำลังตรวจสอบและแก้ไข database...\n")
    fix_invalid_foreign_keys()
    print("\n✨ เสร็จสิ้น! ตอนนี้สามารถรัน migrate ได้แล้ว")
