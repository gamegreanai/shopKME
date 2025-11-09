from django import forms
from django.contrib.auth import authenticate
from .models import User, Profile


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['phone', 'password']


class LoginForm(forms.Form):
    phone = forms.CharField(max_length=10)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        phone = cleaned.get('phone')
        password = cleaned.get('password')
        user = authenticate(phone=phone, password=password)
        if not user:
            raise forms.ValidationError("หมายเลขโทรศัพท์หรือรหัสผ่านไม่ถูกต้อง")
        return cleaned
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "required": True}),
            "last_name":  forms.TextInput(attrs={"class": "form-control", "required": True}),
            "email":      forms.EmailInput(attrs={"class": "form-control", "required": True}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["title", "gender", "phone"]
        widgets = {
            "title":  forms.Select(attrs={"class": "form-select", "required": True}),
            "gender": forms.Select(attrs={"class": "form-select", "required": True}),
            "phone":  forms.TextInput(attrs={
                "class": "form-control",
                "required": True,
                "inputmode": "tel",
                "pattern": r"^0[0-9]{8,9}$",
                "placeholder": "เช่น 0812345678",
            }),
        }

class ProfileAddressForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "house_no",
            "moo",
            "street",
            "subdistrict",
            "district",
            "province",
            "postal_code",
        ]
        widgets = {
            "house_no": forms.TextInput(attrs={"class": "form-control", "placeholder": "เลขที่บ้าน"}),
            "moo": forms.TextInput(attrs={"class": "form-control", "placeholder": "หมู่"}),
            "street": forms.TextInput(attrs={"class": "form-control", "placeholder": "ถนน"}),
            "subdistrict": forms.TextInput(attrs={"class": "form-control", "placeholder": "แขวง/ตำบล"}),
            "district": forms.TextInput(attrs={"class": "form-control", "placeholder": "เขต/อำเภอ"}),
            "province": forms.TextInput(attrs={"class": "form-control", "placeholder": "จังหวัด"}),
            "postal_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "รหัสไปรษณีย์",
                "inputmode": "numeric",
                "pattern": r"^[0-9]{5}$",  # ไทยส่วนใหญ่ 5 หลัก
            }),
        }

    def clean_postal_code(self):
        code = (self.cleaned_data.get("postal_code") or "").strip()
        if code and (not code.isdigit() or len(code) != 5):
            raise forms.ValidationError("รหัสไปรษณีย์ต้องเป็นตัวเลข 5 หลัก")
        return code
    
class AddressForm(forms.Form):
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))


class CombinedProfileForm(forms.Form):
    # User fields (required)
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อ', 'required': 'required'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'นามสกุล', 'required': 'required'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'อีเมล', 'required': 'required'}))

    # Profile fields (required)
    title = forms.ChoiceField(choices=[('นาย','นาย'),('นาง','นาง'),('นางสาว','นางสาว'),('อื่นๆ','อื่นๆ')], required=True, widget=forms.Select(attrs={'class': 'form-select', 'required': 'required'}))
    gender = forms.ChoiceField(choices=[('ชาย','ชาย'),('หญิง','หญิง'),('อื่นๆ','อื่นๆ')], required=True, widget=forms.Select(attrs={'class': 'form-select', 'required': 'required'}))

    house_no = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เลขที่บ้าน', 'required': 'required'}))
    moo = forms.CharField(max_length=10, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'หมู่', 'required': 'required'}))
    street = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ถนน', 'required': 'required'}))
    subdistrict = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'แขวง/ตำบล', 'required': 'required'}))
    district = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เขต/อำเภอ', 'required': 'required'}))
    province = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'จังหวัด', 'required': 'required'}))
    postal_code = forms.CharField(max_length=10, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'รหัสไปรษณีย์', 'required': 'required'}))
    phone = forms.CharField(max_length=10, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เบอร์โทรศัพท์'}))
    def __init__(self, *args, user: User = None, profile: Profile = None, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and user is not None and profile is not None:
            self.initial.update({
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'title': profile.title,
                'gender': profile.gender,
                'house_no': profile.house_no,
                'moo': profile.moo,
                'street': profile.street,
                'subdistrict': profile.subdistrict,
                'district': profile.district,
                'province': profile.province,
                'postal_code': profile.postal_code,
                'phone': user.phone,
            })

    def save(self, user: User, profile: Profile):
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')
        user.phone = self.cleaned_data.get('phone', '') 
        user.save()
        profile.phone = self.cleaned_data.get('phone', '')
        profile.title = self.cleaned_data.get('title', '')
        profile.gender = self.cleaned_data.get('gender', '')
        profile.house_no = self.cleaned_data.get('house_no', '')
        profile.moo = self.cleaned_data.get('moo', '')
        profile.street = self.cleaned_data.get('street', '')
        profile.subdistrict = self.cleaned_data.get('subdistrict', '')
        profile.district = self.cleaned_data.get('district', '')
        profile.province = self.cleaned_data.get('province', '')
        profile.postal_code = self.cleaned_data.get('postal_code', '')
        profile.save()


from django.forms import inlineformset_factory
from .models import Promotion, PromotionImage

class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = [
            "title", "short_text", "description",
            "cover_image",
            "starts_at", "ends_at",
            "active", "priority",
            "min_spend", 
            # "allowed_levels",
            
        ]
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at":   forms.DateTimeInput(attrs={"type": "datetime-local"}),
            # "allowed_levels": forms.Textarea(attrs={"rows": 2, "placeholder": 'เช่น ["SILVER","GOLD"] หรือเว้นว่าง'}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

PromotionImageFormSet = inlineformset_factory(
    parent_model=Promotion,
    model=PromotionImage,
    fields=["image", "alt_text", "sequence"],
    extra=1,
    can_delete=True,
    )