import re
import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

def validate_kenyan_phone(value):
    pattern = r'^2547\d{8}$' 
    if not re.match(pattern, value):
        raise ValidationError("Enter a valid phone number (e.g. 254710000000)")

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('1', 'Admin'),
        ('3', 'Manager'),
        # ('4', 'farmer'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='3')
    email = models.EmailField(unique=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.save()

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
class Profile(models.Model):
    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'), ('O', 'Other'))
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    phone_number = models.CharField(
        max_length=12, blank=True, null=True, validators=[validate_kenyan_phone]
    )
    id_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Emergency Contact (Crucial for Tenants)
    next_of_kin = models.CharField(max_length=255, blank=True, null=True)   
    next_of_kin_phone = models.CharField(
        max_length=12, validators=[validate_kenyan_phone], blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username