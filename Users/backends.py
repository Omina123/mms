from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import CustomUser

class PhoneOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Look for user matching the input in either email or phone_number
            # We look into the Profile for phone_number since it's stored there
            user = CustomUser.objects.get(
                Q(email__iexact=username) | 
                Q(profile__phone_number=username)
            )
        except CustomUser.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None