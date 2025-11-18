from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.validators import MinValueValidator, MaxValueValidator,FileExtensionValidator
from django.utils.text import slugify


# Custom User using phone as username

class Partner(models.Model):
    CATEGORY_CHOICES = [
        ('partner', 'คูปองพาร์ทเนอร์'),
        ('ddream', 'คูปองดีดรีม'),
    ]
    SUBCATEGORY_CHOICES = [
        ('all', 'ทั้งหมด'),
        ('special', 'พิเศษสำหรับคุณ'),
        ('used', 'ใช้แล้ว/หมดอายุ'),
    ]
    
    name = models.CharField(max_length=150, unique=True)
    logo = models.ImageField(
        upload_to="partners/%Y/%m/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )
    title = models.CharField(max_length=255, blank=True, help_text="ข้อมูลเพิ่มเติมเกี่ยวกับพาร์ทเนอร์")
    available_branches = models.TextField(blank=True, help_text="สาขาที่ใช้งานได้")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='partner')
    subcategory = models.CharField(max_length=20, choices=SUBCATEGORY_CHOICES, default='all', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def logo_url(self):
        return self.logo.url if self.logo else ""

class Promotion(models.Model):
    """โปรโมชันสำหรับโชว์ในหน้าเว็บ/แอป อาจผูกคูปองหรือไม่ก็ได้"""
    title       = models.CharField(max_length=200)
    slug        = models.SlugField(max_length=220, unique=True, blank=True)
    short_text  = models.CharField(max_length=255, blank=True)      # คำโปรยสั้น
    description = models.TextField(blank=True)                       # รายละเอียดยาว (เก็บเป็น HTML/Markdown ก็ได้)

    # รูปหลัก
    cover_image = models.ImageField(
        upload_to="promotions/%Y/%m/",
        null=True, blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )

    # เงื่อนไขเวลา/สถานะ
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at   = models.DateTimeField(null=True, blank=True)
    active    = models.BooleanField(default=True)
    priority  = models.IntegerField(default=0, help_text="เลขมากอยู่บน (สำหรับจัดลำดับแสดงผล)")

    # เงื่อนไขทางธุรกิจเบื้องต้น
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                    validators=[MinValueValidator(0)])
    allowed_levels = models.JSONField(default=list, blank=True,
                                      help_text='ตัวอย่าง: ["SILVER","GOLD","PREMIUM"]; เว้นว่าง = ทุกเลเวล')

    # ผูกคูปอง (ถ้ามี) — ไม่บังคับ
    coupon = models.ForeignKey(
        "Coupon",    # เปลี่ยนเป็น app label ของโมดูลที่ประกาศ Coupon
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="promotions"
    )

    # เมตา
    created_by = models.ForeignKey( settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="promotions_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["active", "starts_at", "ends_at"]),
            models.Index(fields=["priority", "active"]),
            models.Index(fields=["slug"]),
        ]
        ordering = ["-priority", "-starts_at", "-id"]

    def __str__(self):
        return self.title

    # ---------- hooks ----------
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "promotion"
            cand = base
            i = 1
            while Promotion.objects.filter(slug=cand).exclude(pk=self.pk).exists():
                i += 1
                cand = f"{base}-{i}"
            self.slug = cand
        super().save(*args, **kwargs)

    # ---------- helpers ----------
    def is_active_now(self) -> bool:
        now = timezone.now()
        if not self.active or self.is_deleted:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    def cover_url(self) -> str:
        return self.cover_image.url if self.cover_image else ""

    def level_allowed(self, user) -> bool:
        # อิง enum เดิมของคุณ: MembershipLevel.values
        if not self.allowed_levels:
            return True
        try:
            # ดึงแต้มจากโปรไฟล์แล้วแปลงเป็นเลเวล ด้วยฟังก์ชันเดิม
            from .models import level_from_points  # ปรับ path ให้ตรง
            points = getattr(getattr(user, "profile", None), "points", 0)
            level = level_from_points(points)
            return level in self.allowed_levels
        except Exception:
            return True  # ถ้าไม่มีโปรไฟล์ให้ผ่านไปก่อน

    def can_show_to(self, user, subtotal=None) -> bool:
        """ใช้เช็คก่อนแสดงผล/ให้กดรับ—โฟกัสแค่เงื่อนไขทั่วไป"""
        if not self.is_active_now():
            return False
        if user and not self.level_allowed(user):
            return False
        if subtotal is not None and self.min_spend and subtotal < self.min_spend:
            return False
        return True


class PromotionImage(models.Model):
    """แกลเลอรีรูปของโปรโมชัน"""
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(
        upload_to="promotions/gallery/%Y/%m/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )
    alt_text = models.CharField(max_length=200, blank=True)
    sequence = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sequence", "id"]

    def __str__(self):
        return f"Image of {self.promotion_id}"

    def url(self):
        return self.image.url if self.image else ""


class PromotionTracking(models.Model):
    """เก็บสถิติการดู/คลิก—เผื่อทำรีพอร์ตง่าย ๆ (ไม่บังคับใช้)"""
    VIEW  = "view"
    CLICK = "click"
    ACTION_CHOICES = [(VIEW, "view"), (CLICK, "click")]

    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name="tracks")
    action    = models.CharField(max_length=10, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,   
        null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["promotion", "action", "at"]),
        ]

class User(AbstractUser):
    phone = models.CharField(max_length=10, unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone


class Profile(models.Model):
    TITLE_CHOICES = [
        ('นาย', 'นาย'),
        ('นาง', 'นาง'),
        ('นางสาว', 'นางสาว'),
        ('อื่นๆ', 'อื่นๆ'),
    ]

    GENDER_CHOICES = [
        ('ชาย', 'ชาย'),
        ('หญิง', 'หญิง'),
        ('อื่นๆ', 'อื่นๆ'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # ชื่อ-สกุล (first_name/last_name/email อยู่ใน User แล้ว)
    title = models.CharField(max_length=20, choices=TITLE_CHOICES, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    phone = models.IntegerField(blank=True, null=True)
    # คะแนน
    points = models.PositiveIntegerField(default=0)

    # ที่อยู่ (แยกส่วน)
    house_no = models.CharField(max_length=50, blank=True)
    moo = models.CharField(max_length=10, blank=True)
    street = models.CharField(max_length=100, blank=True)
    subdistrict = models.CharField(max_length=100, blank=True)  # แขวง/ตำบล
    district = models.CharField(max_length=100, blank=True)     # เขต/อำเภอ
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"Profile of {self.user.phone}"


# For get_user_model usages
User = get_user_model()


def default_expiry_date():
    return timezone.now() + timedelta(days=30)

class PointTransaction(models.Model):
    ACTION_CHOICES = [
        ('add', 'เพิ่มแต้ม'),
        ('subtract', 'ลบแต้ม'),
    ]
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='transactions_made')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions_received')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    points = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff} {self.get_action_display()} {self.points} แต้ม ให้ {self.user}"


class MembershipLevel(models.TextChoices):
    SILVER  = "SILVER",  "Silver"
    GOLD    = "GOLD",    "Gold"
    PREMIUM = "PREMIUM", "Premium"

def level_from_points(points: int) -> str:
    pts = points or 0
    if pts >= 1000:
        return MembershipLevel.PREMIUM
    elif pts >= 500 and pts < 1000:
        return MembershipLevel.GOLD
    else:
        return MembershipLevel.SILVER

class Coupon(models.Model):
    PERCENT = "PERCENT"
    FIXED   = "FIXED"

    DISCOUNT_TYPE_CHOICES = [
        (PERCENT, "เปอร์เซ็นต์"),
        (FIXED,   "จำนวนเงินคงที่"),
    ]
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=40, unique=True, db_index=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    # optional cap เมื่อเป็นเปอร์เซ็นต์
    percent_max_discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="จำกัดส่วนลดสูงสุดเมื่อเป็นเปอร์เซ็นต์ (ไม่บังคับ)"
    )

    min_spend = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)]
    )

    starts_at = models.DateTimeField(default=timezone.now)
    ends_at   = models.DateTimeField(null=True, blank=True)

    active = models.BooleanField(default=True)
    note = models.CharField(max_length=255, blank=True)

    # เลเวลของผู้ใช้ที่ใช้คูปองนี้ได้ (อย่างน้อย 1 ค่า)
    allowed_levels = models.JSONField(
        default=list,
        help_text="ตัวอย่าง: [\"SILVER\", \"GOLD\"]"
    )

    # จำกัดจำนวนการใช้
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="ทั้งหมดกี่ครั้ง (เว้นว่าง=ไม่จำกัด)")
    use_count = models.PositiveIntegerField(default=0)

    max_uses_per_user = models.PositiveIntegerField(null=True, blank=True, help_text="ต่อผู้ใช้กี่ครั้ง (เว้นว่าง=ไม่จำกัด)")

    # ปิดการซ้อนคูปองได้ถ้ามี requirement ภายหน้า
    stackable = models.BooleanField(default=False)
    required_points = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(
        upload_to="coupons/%Y/%m/",
        null=True, blank=True,
        validators=[FileExtensionValidator(["jpg","jpeg","png","webp"])],
    )
    image_code = models.ImageField(
        upload_to="coupons_qr/%Y/%m/",
        null=True, blank=True,
        validators=[FileExtensionValidator(["jpg","jpeg","png","webp"])],
    )
    available_branches = models.TextField(blank=True, help_text="สาขาที่ใช้งานได้")
    partner = models.ForeignKey(
        Partner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupons",
        help_text="พาร์ทเนอร์ที่เป็นเจ้าของคูปองนี้"
    )
    is_deleted = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["active", "starts_at", "ends_at"]),
        ]

    def __str__(self):
        return f"{self.code} ({self.discount_type}:{self.discount_value})"

    # ---------- Validation ----------
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.discount_type == self.PERCENT:
            # 0 < value <= 100
            if not (0 < float(self.discount_value) <= 100):
                raise ValidationError("เปอร์เซ็นต์ต้องอยู่ในช่วง 0–100")
        # วันหมดอายุ
        if self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError("วันสิ้นสุดต้องมากกว่าวันเริ่มต้น")
        # allowed_levels ต้องเป็นค่าที่อยู่ใน enum
        invalid = [lv for lv in (self.allowed_levels or []) if lv not in MembershipLevel.values]
        if invalid:
            raise ValidationError(f"allowed_levels ไม่ถูกต้อง: {invalid}")

    # ---------- Logic ----------
    def is_active_now(self):
        now = timezone.now()
        if not self.active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        if self.max_uses is not None and self.use_count >= self.max_uses:
            return False
        return True

    def user_level(self, user: User) -> str:
        # สมมติคุณมี Profile.points
        points = getattr(getattr(user, "profile", None), "points", 0)
        return level_from_points(points)

    def user_usage_count(self, user: User) -> int:
        return self.redemptions.filter(user=user).count()

    def is_user_eligible(self, user: User) -> bool:
        level = self.user_level(user)
        return level in (self.allowed_levels or [])

    def can_user_use(self, user: User) -> bool:
        if not self.is_active_now():
            return False
        if not self.is_user_eligible(user):
            return False
        if self.max_uses_per_user is not None and self.user_usage_count(user) >= self.max_uses_per_user:
            return False
        return True
    
    def image_url(self):
        return self.image.url if self.image else ""
    
    def compute_discount(self, subtotal):
        """คืนจำนวนเงินส่วนลดตามประเภท"""
        from decimal import Decimal
        subtotal = Decimal(subtotal)
        if subtotal < (self.min_spend or 0):
            return Decimal("0.00")
        if self.discount_type == self.PERCENT:
            amt = (subtotal * self.discount_value) / Decimal("100")
            if self.percent_max_discount is not None:
                amt = min(amt, self.percent_max_discount)
            return max(amt, Decimal("0.00"))
        # FIXED
        return max(Decimal(self.discount_value), Decimal("0.00"))

class CouponRedemption(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="redemptions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="coupon_redemptions")
    order_id = models.CharField(max_length=64, blank=True)  # อ้างอิงคำสั่งซื้อถ้ามี
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("coupon", "user", "order_id")]  # ป้องกัน apply ซ้ำบนออเดอร์เดียวกัน
        indexes = [
            models.Index(fields=["user", "coupon"]),
        ]

    def __str__(self):
        return f"{self.coupon.code} @ {self.user_id} ({self.discount_applied})"


class CouponSlideImage(models.Model):
    """Model สำหรับเก็บรูปภาพคูปองแบบสไลด์/แบนเนอร์"""
    name = models.CharField(max_length=255, help_text="ชื่อรูปภาพ")
    image = models.ImageField(
        upload_to="coupon_slides/%Y/%m/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
        help_text="รูปภาพคูปอง"
    )
    partner = models.ForeignKey(
        "Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="slide_images",
        help_text="เชื่อมโยงกับพาร์ทเนอร์ (คลิกรูปจะแสดงคูปอง)"
    )
    sort_order = models.IntegerField(default=0, help_text="ลำดับการแสดงผล (น้อยไปมาก)")
    is_active = models.BooleanField(default=True, help_text="สถานะการใช้งาน")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "รูปภาพคูปอง"
        verbose_name_plural = "รูปภาพคูปอง"

    def __str__(self):
        partner_info = f" ({self.partner.name})" if self.partner else ""
        return f"{self.name}{partner_info}"

    def image_url(self):
        return self.image.url if self.image else ""

