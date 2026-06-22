import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from Users.models import CustomUser
from django.db import transaction, models
from django.core.exceptions import ValidationError

# 1. PHONE VALIDATOR
from django.core.validators import RegexValidator

kenyan_phone_validator = RegexValidator(
    # Matches +254..., 254..., or 0... 
    # Followed by 7xx or 1xx and then 7 digits
    regex=r'^(?:\+254|254|0)((?:[7][0-24-9]|[1][0-1])\d{7})$',
    message="Enter a valid Kenyan number (e.g., 0712345678, 254712345678, or +254712345678)"
)

# 2. FARMER MODEL
import uuid
from django.db import models

class Farmer(models.Model):
    farmer_id = models.CharField(max_length=15, unique=True, editable=False)
    name = models.CharField(max_length=100)
    # Using the updated validator we discussed
    phone_number = models.CharField(validators=[kenyan_phone_validator], max_length=15)
    location = models.CharField(max_length=100, blank=True)
    
    # Financial Balances
    milling_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    milking_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    joined_date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 1. Generate Farmer ID if it doesn't exist
        if not self.farmer_id:
            self.farmer_id = f"FMR-{uuid.uuid4().hex[:5].upper()}"
        
        # 2. Normalize Phone Number to +254... format
        # Strip any spaces just in case
        phone = self.phone_number.replace(" ", "")
        
        if phone.startswith('0'):
            # Convert 0712... to +254712...
            self.phone_number = '+254' + phone[1:]
        elif phone.startswith('254'):
            # Convert 254712... to +254712...
            self.phone_number = '+' + phone
        elif phone.startswith('+254'):
            # Already correct
            self.phone_number = phone
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.farmer_id})"

# --- MILLING SECTION (Intake -> Store -> Batch -> Shop) ---

class MaizeIntake(models.Model):
    """The Link: Recording what the farmer brings to the store"""
    intake_no = models.CharField(max_length=20, unique=True, editable=False)
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='maize_deliveries')
    sacks_delivered = models.PositiveIntegerField()
    price_per_sack = models.DecimalField(max_digits=10, decimal_places=2)
    total_credit = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.intake_no:
            self.intake_no = f"IN-{uuid.uuid4().hex[:6].upper()}"
        self.total_credit = self.sacks_delivered * self.price_per_sack
        super().save(*args, **kwargs)

class MaizeStore(models.Model):
    """The 'Bank' for Raw Maize Sacks (Global Inventory)"""
    total_sacks = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Global Store: {self.total_sacks} Sacks"

import uuid
from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

class MillingBatch(models.Model):
    batch_no = models.CharField(max_length=20, unique=True, editable=False)
    date = models.DateTimeField(default=timezone.now)
    sacks_pulled_from_store = models.PositiveIntegerField()
    
    # Outputs (Recorded as raw units/quantities)
    one_kg_flour_bales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    two_kg_flour_bales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maize_germ_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maize_bran_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def clean(self):
        """
        Simple Balance: Total Output Units must equal Total Input Units.
        No KG conversions applied.
        """
        total_input = Decimal(self.sacks_pulled_from_store)
        
        # Summing up exactly what was typed into the output fields
        total_output = (
            Decimal(self.one_kg_flour_bales) + 
            Decimal(self.two_kg_flour_bales) + 
            Decimal(self.maize_germ_kg) + 
            Decimal(self.maize_bran_kg)
        )

        if total_input != total_output:
            raise ValidationError(
                f"Balance Error: Input ({total_input}) does not match Total Output ({total_output}). "
                f"These numbers must be equal."
            )

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.batch_no:
            self.batch_no = f"ML-{uuid.uuid4().hex[:6].upper()}"

        with transaction.atomic():
            # 1. Deduct from MaizeStore
            from .models import MaizeStore, ProductStock # Ensure imports are correct
            store = MaizeStore.objects.select_for_update().first()
            
            if not store or store.total_sacks < self.sacks_pulled_from_store:
                raise ValidationError(f"Insufficient sacks in store!")
            
            if not self.pk: 
                store.total_sacks -= self.sacks_pulled_from_store
                store.save()

                # 2. Update Product Stock with exact numbers entered
                stock_map = [
                    ('FLOUR1', self.one_kg_flour_bales),
                    ('FLOUR2', self.two_kg_flour_bales),
                    ('GERM', self.maize_germ_kg),
                    ('BRAN', self.maize_bran_kg),
                ]

                for p_type, qty in stock_map:
                    if qty > 0:
                        product, _ = ProductStock.objects.get_or_create(product_type=p_type)
                        product.quantity = Decimal(str(product.quantity)) + Decimal(str(qty))
                        product.save()

        super().save(*args, **kwargs)

import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone

class MilkCollection(models.Model):
    # Auto-generated unique number
    collection_no = models.CharField(max_length=20, unique=True, editable=False)

    farmer = models.ForeignKey('Farmer', on_delete=models.CASCADE, related_name='milk_collections')
    litres = models.DecimalField(max_digits=10, decimal_places=2)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Selling price per litre")
    # total_cost = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # 1. Generate reference number once
        if not self.collection_no:
            self.collection_no = f"MLK-{uuid.uuid4().hex[:6].upper()}"

        # 2. Always compute total cost (NO SIDE EFFECTS)
        self.total_cost = (
            Decimal(str(self.litres)) *
            Decimal(str(self.buying_price))
        )

        # 3. ONLY save record (NO STOCK, NO BALANCE LOGIC HERE)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.collection_no} - {self.farmer.name} ({self.litres}L)"

    class Meta:
        verbose_name = "Milk Collection"
        verbose_name_plural = "Milk Collections"
        ordering = ['-date']
# --- FINANCIALS & SALES SECTION ---
class MpesaTransaction(models.Model):
    """Bridge for all M-Pesa movements (C2B or B2C)"""
    TRANSACTION_TYPES = [('PAYMENT', 'Customer Payment'), ('PAYOUT', 'Farmer Payout')]
    
    merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    transaction_no = models.CharField(max_length=50, unique=True, null=True, blank=True) # The actual M-Pesa Code
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, default='PENDING') # PENDING, COMPLETED, FAILED
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_no} - {self.amount}"

# --- GENERAL SHOP ITEMS SECTION ---

class ShopItem(models.Model):
    """Catalog of general commodities (Sugar, Rice, Cooking oil, etc.)"""
    name = models.CharField(max_length=100, unique=True, help_text="e.g., Sugar (1kg), Rice (25kg)")
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Stock Keeping Unit / Barcode")
    buying_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Wholesale buying price")
    default_selling_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Standard retail price")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ShopItemStock(models.Model):
    """Tracks physical inventory levels for general shop commodities"""
    item = models.OneToOneField(ShopItem, on_delete=models.CASCADE, related_name='stock')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Available items/kg in store")
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, help_text="Alert when stock dips below this")
    last_restocked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.name}: {self.quantity} available"
from django.db import transaction, models
from django.core.exceptions import ValidationError
class ProductSale(models.Model):
    PRODUCT_CHOICES = [
        ('FLOUR1', 'Unga Bale 1 kg'),
        ('FLOUR2', 'Unga Bale 2 kg'),
        ('GERM', 'Maize Germ'),
        ('BRAN', 'Maize Bran'),
        ('MILK', 'Fresh Milk'),
        ('OTHER', 'General Shop Item'), # Added choice to route to general shop items
    ]

    STATUS_CHOICES = [
        ('PAID', 'Paid / Cash'),
        ('CREDIT', 'On Credit'),
        ('PENDING', 'Pending')
    ]

    product = models.CharField(max_length=10, choices=PRODUCT_CHOICES)
    
    # NEW LINK: Optional relationship to a general shop item
    shop_item = models.ForeignKey(ShopItem, on_delete=models.SET_NULL, null=True, blank=True, help_text="Fill this ONLY if product is 'General Shop Item'")
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    payment_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PAID')
    customer_name = models.CharField(max_length=100, blank=True, null=True, help_text="Who bought on credit?")
    sold_at = models.DateTimeField(auto_now_add=True)
    
    payment_method = models.CharField(
        max_length=10, 
        choices=[('CASH', 'Cash'), ('MPESA', 'M-Pesa'), ('CREDIT', 'Credit')], 
        default='CASH'
    )
    mpesa_record = models.OneToOneField(MpesaTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    mpesa_checkout_id = models.CharField(max_length=100, null=True, blank=True)

    def clean(self):
        # Validation to ensure data consistency
        if self.product == 'OTHER' and not self.shop_item:
            raise ValidationError("You selected 'General Shop Item'. Please specify which item was sold in the 'shop_item' field.")
        if self.product != 'OTHER' and self.shop_item:
            raise ValidationError("You cannot pick a specific milling product and link a general shop item at the same time.")

    def save(self, *args, **kwargs):
        # 1. Run validation rules first
        self.full_clean()
        
        # 2. Compute total cost
        self.total_revenue = Decimal(str(self.quantity)) * Decimal(str(self.selling_price))
        
        # 3. Handle stock deductions atomically for new entries
        if not self.pk:
            with transaction.atomic():
                if self.product == 'OTHER':
                    # Deduct from dynamic shop stock
                    stock = ShopItemStock.objects.select_for_update().get(item=self.shop_item)
                    if stock.quantity < self.quantity:
                        raise ValidationError(f"Insufficient stock for {self.shop_item.name}! Available: {stock.quantity}")
                    stock.quantity -= self.quantity
                    stock.save()
                else:
                    # Deduct from traditional processed stock
                    stock = ProductStock.objects.select_for_update().get(product_type=self.product)
                    if stock.quantity < self.quantity:
                        raise ValidationError(f"Insufficient {self.get_product_display()} stock!")
                    stock.quantity -= self.quantity
                    stock.save()

        super().save(*args, **kwargs)

    def __str__(self):
        if self.product == 'OTHER' and self.shop_item:
            return f"{self.shop_item.name} - {self.quantity} @ {self.sold_at.strftime('%H:%M')}"
        return f"{self.get_product_display()} - {self.quantity} @ {self.sold_at.strftime('%H:%M')}"

from django.db import models, transaction

class FarmerPayment(models.Model):
    """Payouts TO farmers (Reducing the balance)"""
    CATEGORY_CHOICES = [('MILK', 'Milk'), ('MAIZE', 'Maize')]
    
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=50, help_text="M-Pesa Ref")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='MILK')
    date = models.DateTimeField(auto_now_add=True)
    mpesa_payout = models.OneToOneField(MpesaTransaction, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        # We wrap this in a transaction to ensure both records update or none do
        if not self.pk:  # Only deduct balance on the first save (creation)
            with transaction.atomic():
                if self.category == 'MILK':
                    self.farmer.milking_balance -= self.amount
                else:
                    self.farmer.milling_balance -= self.amount
                
                self.farmer.save() # This is the missing link!
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.farmer.name} - {self.amount} ({self.category})"
class ActivityLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50) 
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
class ProductStock(models.Model):
    PRODUCT_CHOICES = [
        ('FLOUR1', 'Unga 1 kg Bale'),
        ('FLOUR2', 'Unga 2 kg Bale'),
        ('GERM', 'Maize Germ'),
        ('BRAN', 'Maize Bran'),
        ('MILK', 'Fresh Milk'),
    ]
    product_type = models.CharField(max_length=10, choices=PRODUCT_CHOICES, unique=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Current selling price per unit"
    )
# 3. MPESA TRANSACTION TRACKER
