from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile, validate_kenyan_phone

class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    middle_name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=12, validators=[validate_kenyan_phone])
    id_number = forms.CharField(max_length=20, required=False)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'middle_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.middle_name = self.cleaned_data['middle_name']

        # Using phone number as username for unique identification
        user.username = self.cleaned_data['phone_number']
        user.user_type = '3'  # Default to Manager/Staff level

        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number'),
                id_number=self.cleaned_data.get('id_number')
            )
        return user

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Email or Phone Number", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Phone or Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['user_type','username', 'email', 'first_name', 'last_name', 'middle_name']
        widgets = {
            # This 'form-select' class is what makes it look modern in Bootstrap 5
            'user_type': forms.Select(attrs={'class': 'form-select form-select-lg border-primary'}),
        }