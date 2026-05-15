from django import forms
from .models import *
from django import forms
from .models import MaizeIntake, Farmer

class MaizeIntakeForm(forms.ModelForm):
    farmer = forms.ModelChoiceField(
        queryset=Farmer.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select glass-input'}),
        empty_label="Select Supplier"
    )

    class Meta:
        model = MaizeIntake
        fields = ['farmer', 'sacks_delivered', 'price_per_sack']
        widgets = {
            'sacks_delivered': forms.NumberInput(attrs={
                'class': 'form-control glass-input', 
                'placeholder': 'Quantity in Sacks',
                'id': 'id_sacks'
            }),
            'price_per_sack': forms.NumberInput(attrs={
                'class': 'form-control glass-input', 
                'placeholder': 'Price per Sack',
                'id': 'id_price'
            }),
        }
from django import forms
from .models import Farmer

class FarmerForm(forms.ModelForm):
    class Meta:
        model = Farmer
        fields = ['name', 'phone_number', 'location']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control glass-input', 
                'placeholder': 'e.g. John Doe'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control glass-input', 
                'placeholder': '0712345678 or 254...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control glass-input', 
                'placeholder': 'e.g. Eldoret'
            }),
        }
        help_texts = {
            'phone_number': 'Accepts 07..., 254..., or +254...'
        }

class MillingBatchForm(forms.Form):
    sacks_input = forms.IntegerField(
        min_value=1, 
        label="Sacks Pulled",
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': '0'})
    )
    unga_one_kg_output = forms.IntegerField(
        min_value=0, 
        label="Unga One Kg Bales",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'})
    )
    unga_two_kg_output = forms.IntegerField(
        min_value=0, 
        label="Unga Two Kg Bales",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'})
    )
    germ_output = forms.FloatField(
        min_value=0, 
        label="Maize Germ (KG)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.0'})
    )
    bran_output = forms.FloatField(
        min_value=0, 
        label="Maize Bran (KG)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.0'})
    )
from django import forms
from .models import ProductSale

class ProductSaleForm(forms.ModelForm):
    class Meta:
        model = ProductSale
        fields = ['product', 'quantity', 'selling_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price per unit'}),
        }
        labels = {
            'product': 'Select Item',
            'selling_price': 'Unit Price (KES)',
        }


class ProductSaleForm(forms.ModelForm):
    class Meta:
        model = ProductSale
        fields = ['product', 'quantity', 'selling_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price per unit'}),
        }


class MilkCollectionForm(forms.ModelForm):
    class Meta:
        model = MilkCollection
        fields = ['farmer', 'litres', 'buying_price', 'date']
        widgets = {
            'farmer': forms.Select(attrs={'class': 'form-select select2'}),
            'litres': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'buying_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 50'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }