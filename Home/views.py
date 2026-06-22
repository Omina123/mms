from django.shortcuts import get_object_or_404, render,redirect
from django.conf import settings
from .models import *
from django.contrib import messages
from .forms import*
from .models import ActivityLog
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg, Sum,F,Q
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

#from Home.utlis import send_intake_sms # Import your new helper
from django.http import JsonResponse
# Create your views here.
def home(request):
    return render(request, "home/index.html")
def About(request):
    return render(request, "home/about.html")
def Services(request):
    return render(request, "home/service.html")
def Contact(request):
    # if request.method == "POST":
    #     name = request.POST.get("name")
    #     email = request.POST.get("email")
    #     subject = request.POST.get("subject")
    #     message = request.POST.get("message")
    #     contact = ContactUs(name=name, email=email, subject=subject, message=message)
    #     contact.save()
    #     messages.success(request, "Your message has been sent successfully!")
    #     return redirect('contact')
    return render(request, "contact.html")
from django.db.models import Sum
from .models import MaizeStore, ProductStock, ProductSale, MilkCollection
from django.contrib.auth.decorators import login_required, user_passes_test
def is_admin(user):
    # Check if user is logged in AND is either a superuser or admin type
    if user.is_authenticated:
        return user.is_superuser or getattr(user, 'user_type', None) == '1'
    return False
@login_required(login_url='/login/')
@user_passes_test(is_admin)
def Admin(request):
    store = MaizeStore.objects.first()
    stock_qs = ProductStock.objects.all()
    stocks = {s.product_type: s.quantity for s in stock_qs}
    
    context = {
        'raw_stock': store.total_sacks if store else 0,
        'live_unga': stocks.get('FLOUR1', 0),
        'live_unga_2kg': stocks.get('FLOUR2', 0),
        'live_germ': stocks.get('GERM', 0),
        'live_bran': stocks.get('BRAN', 0),
        'live_milk': stocks.get('MILK', 0),
        # Display only the 3 most recent sales
        'recent_sales': ProductSale.objects.all().order_by('-sold_at')[:3],
    }
    return render(request, "admin.html", context)
from django.shortcuts import render
from .models import ProductSale, MaizeStore, ProductStock
from django.shortcuts import render
from django.db.models import Sum
from django.utils.dateparse import parse_date
import datetime
from .models import ProductSale

def sales_report(request):
    """View to display filtered or full history of sales and invoices"""
    # Fetch base queryset
    all_sales = ProductSale.objects.all().order_by('-sold_at')
    
    # Get date filters from request GET parameters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None

    # Apply date range filtering if both limits are present
    if start_date and end_date:
        # Make the end_date inclusive of the entire day (up to 23:59:59)
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
        all_sales = all_sales.filter(sold_at__range=(start_date, end_datetime))
        
    # Calculate totals for the report header dynamically based on the filtered results
    # Using aggregate is much faster than running a Python loop over large databases
    total_revenue = all_sales.aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0
    
    context = {
        'all_sales': all_sales,
        'total_revenue': total_revenue,
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, "sales_report.html", context)
def manager_dashboard(request):
    # 1. Raw Maize Stock (Sacks waiting to be milled)
    store = MaizeStore.objects.first()
    raw_stock = store.total_sacks if store else 0

    # 2. Live Inventory (Actual stock available for sale right now)
    stock_qs = ProductStock.objects.all()
    stocks = {s.product_type: s.quantity for s in stock_qs}

    # 3. Get milk stock
    milk_stock = ProductStock.objects.filter(product_type='MILK').first()

    # 4. Recent Milling Batches (Production History)
    recent_batches = MillingBatch.objects.all().order_by('-date')[:5]
    
    # 5. Recent Sales - Get ONLY ONCE
    recent_sales = ProductSale.objects.all().order_by('-sold_at')[:10]
    
    # 6. Recent Milk Collections - Get ONLY ONCE
    recent_milk = MilkCollection.objects.all().order_by('-date')[:5]

    context = {
        'raw_stock': raw_stock,
        'live_unga_1kg': stocks.get('FLOUR1', 0), 
        'live_unga_2kg': stocks.get('FLOUR2', 0),
        'live_germ': stocks.get('GERM', 0), 
        'live_bran': stocks.get('BRAN', 0), 
        'recent_batches': recent_batches,
        'recent_sales': recent_sales,  # ONLY ONCE
        'live_milk': milk_stock.quantity if milk_stock else 0,
        'recent_milk': recent_milk,  # ONLY ONCE
        'milk_form': MilkCollectionForm(),
        'shop_items_stock': ShopItemStock.objects.all().select_related('item').order_by('quantity'),
    }
    return render(request, 'manager_dashboard.html', context)
def add_farmer(request):
    if request.method == "POST":
        form = FarmerForm(request.POST)
        if form.is_valid():
            # Save the farmer
            farmer = form.save()

            # Create the Activity Log entry
            ActivityLog.objects.create(
                user=request.user,
                action='CREATE',
                description=f"Added Farmer: {farmer.name} ({farmer.farmer_id})",
                content_type=ContentType.objects.get_for_model(farmer),
                object_id=farmer.id
            )

            messages.success(request, f"Farmer {farmer.name} added successfully!")
            return redirect('manager_dashboard') # Redirect to your list of farmers
    else:
        form = FarmerForm()
    
    return render(request, 'add_farmers.html', {'form': form})

#from Home.utlis import send_intake_sms # Import your new helper
from .utlis import send_infobip_sms
def record_maize_intake(request):
    if request.method == "POST":
        form = MaizeIntakeForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Process Intake
                    intake = form.save(commit=False)
                    intake.total_credit = intake.sacks_delivered * intake.price_per_sack
                    intake.save()

                    # 2. Update Farmer Balance
                    farmer = intake.farmer
                    farmer.milling_balance += intake.total_credit
                    farmer.save()

                    # 3. Update Global Store
                    store, _ = MaizeStore.objects.get_or_create(id=1)
                    store.total_sacks += intake.sacks_delivered
                    store.save()

                # --- SMS SENDING (Outside atomic block for safety) ---
                # Strip '+' for Infobip API
                clean_phone = str(farmer.phone_number).replace('+', '')
                msg = (f"Hello {farmer.name}, received {intake.sacks_delivered} sacks. "
                       f"Credit: Ksh {intake.total_credit}. New milling bal: Ksh {farmer.milling_balance}")
                
                send_infobip_sms(clean_phone, msg)

                messages.success(request, f"Successfully recorded {intake.sacks_delivered} sacks.")
                return redirect('maize_intake_list')
                
            except Exception as e:
                messages.error(request, f"System Error: {str(e)}")
        else:
            messages.error(request, "Please check your input data.")
    else:
        form = MaizeIntakeForm()
    
    return render(request, 'record_intake.html', {'form': form})

def maize_intake_list(request):
    # Fetching all records, ordering by latest first
    intakes = MaizeIntake.objects.all().order_by('-date') 
    
    return render(request, 'maize_list.html', {'intakes': intakes})
def Admin_maize_intake_list(request):
    # Fetching all records, ordering by latest first
    intakes = MaizeIntake.objects.all().order_by('-date') 
    
    return render(request, 'admin_maize intake_list.html', {'intakes': intakes})
def Admin_record_maize_intake(request):
    form = MaizeIntakeForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Maize intake recorded successfully!")
        return redirect('Admin_maize_intake_list')
    return render(request, 'admin_record_intake.html', {'form': form})
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.db import transaction
# from django.core.exceptions import ValidationError

def process_milling_batch(request):
    store = MaizeStore.objects.first()
    raw_stock = store.total_sacks if store else 0

    if request.method == "POST":
        form = MillingBatchForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Initialize the model instance
                    batch = MillingBatch(
                        sacks_pulled_from_store=form.cleaned_data['sacks_input'],
                        one_kg_flour_bales=form.cleaned_data['unga_one_kg_output'],
                        two_kg_flour_bales=form.cleaned_data['unga_two_kg_output'],
                        maize_germ_kg=form.cleaned_data['germ_output'],
                        maize_bran_kg=form.cleaned_data['bran_output']
                    )
                    
                    # 2. Trigger validation (Mass Balance)
                    # We use full_clean() so it hits the clean() method in models.py
                    batch.full_clean() 
                    
                    # 3. Save (Updates inventory)
                    batch.save()

                messages.success(request, f"✅ Batch {batch.batch_no} processed successfully!")
                return redirect('manager_dashboard')

            except ValidationError as e:
                # CLEANING THE MESSAGE:
                # If the error is in a dictionary format (like __all__), extract the text.
                if hasattr(e, 'message_dict'):
                    # Get the list of errors for '__all__', default to the string if missing
                    error_list = e.message_dict.get('__all__', [str(e)])
                    error_msg = error_list[0]
                else:
                    error_msg = str(e)
                
                # Strip any remaining technical characters just in case
                error_msg = error_msg.replace("['", "").replace("']", "")
                
                messages.error(request, f"Rejected: {error_msg}")
                
            except Exception as e:
                messages.error(request, f"System Error: {str(e)}")
    else:
        form = MillingBatchForm()

    context = {
        'form': form, 
        'raw_stock': raw_stock
    }
    return render(request, 'milling_form.html', context)


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# @csrf_exempt
# def mpesa_callback(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         result_code = data['Body']['stkCallback']['ResultCode']
        
#         # ResultCode 0 means SUCCESS
#         if result_code == 0:
#             # Extract the Reference (e.g., S2916)
#             # Safaricom sends the reference in the 'AccountReference' or via custom logic
#             # For simplicity, we usually match via the CheckoutRequestID
#             checkout_id = data['Body']['stkCallback']['CheckoutRequestID']
            
#             try:
#                 # Find the sale and mark as COMPLETED
#                 # (Assumes you saved the CheckoutRequestID in your ProductSale model)
#                 sale = ProductSale.objects.get(mpesa_checkout_id=checkout_id)
#                 sale.payment_status = 'COMPLETED'
#                 sale.save()
#             except ProductSale.DoesNotExist:
#                 pass

#         return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})

def print_receipt(request, sale_id):
    sale = get_object_or_404(ProductSale, id=sale_id)
    return render(request, 'recei_print.html', {'sale': sale})
from django.db import transaction
from .mpesa_utilis import trigger_stk_push  # Ensure you import your utility function

from datetime import datetime
import json
from decimal import Decimal, ROUND_HALF_UP
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect
import json
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import ProductSale
from .mpesa_utilis import trigger_stk_push   # your M‑Pesa utility

# -------------------------------------------------------------------
# Helper to render the sales dashboard (DRY)
# -------------------------------------------------------------------
def _render_sales_dashboard(request, form):
    recent_sales = ProductSale.objects.all().order_by('-sold_at')[:10]

    paid_total = ProductSale.objects.filter(
        Q(payment_status='PAID') | Q(payment_status='COMPLETED')
    ).aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0

    credit_total = ProductSale.objects.filter(
        payment_status='CREDIT'
    ).aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0

    return render(request, 'sales.html', {
        'form': form,
        'paid_total': paid_total,
        'credit_total': credit_total,
        'recent_sales': recent_sales,
    })

# -------------------------------------------------------------------
# Record Sale (handles multi‑item cart)
# -------------------------------------------------------------------
def record_sale(request):
    if request.method == "POST":
        # AJAX / JSON submission from the cart
        if request.headers.get('Content-Type') == 'application/json' or \
           request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                cart_items = data.get('items', [])
                payment_method = data.get('payment_method', 'CASH')
                customer_phone = data.get('customer_phone')
                customer_name = data.get('customer_name')

                if not cart_items:
                    return JsonResponse(
                        {'status': 'error', 'message': 'Your cart is completely empty.'},
                        status=400
                    )

                if payment_method == 'MPESA' and not customer_phone:
                    return JsonResponse(
                        {'status': 'error', 'message': 'Mobile phone number is required for M-Pesa STK push.'},
                        status=400
                    )

                total_order_revenue = Decimal('0.00')
                saved_sales = []

                with transaction.atomic():
                    for item in cart_items:
                        shop_item_id = item.get('shop_item')

                        # Create a new sale instance (no form used)
                        sale = ProductSale()
                        sale.product = item.get('product')
                        if shop_item_id and sale.product == 'OTHER':
                            sale.shop_item_id = int(shop_item_id)

                        # Quantities and prices sent from frontend
                        kg_quantity = Decimal(str(item.get('quantity', 0)))
                        kg_price = Decimal(str(item.get('selling_price', 0)))

                        # Compute line total
                        sale.total_revenue = (kg_quantity * kg_price).quantize(
                            Decimal('0.01'), rounding=ROUND_HALF_UP
                        )
                        total_order_revenue += sale.total_revenue

                        sale.quantity = kg_quantity
                        sale.selling_price = kg_price

                        # Set payment status and method
                        if payment_method == 'CREDIT':
                            sale.payment_status = 'CREDIT'
                            sale.payment_method = 'CREDIT'
                            sale.customer_name = customer_name   # now saved!
                        elif payment_method == 'MPESA':
                            sale.payment_status = 'PENDING'
                            sale.payment_method = 'MPESA'
                        else:   # CASH
                            sale.payment_status = 'PAID'
                            sale.payment_method = 'CASH'

                        sale.save()
                        saved_sales.append(sale)

                # -------------------------------------------------------------------
                # If M‑Pesa, initiate STK push for the whole cart
                # -------------------------------------------------------------------
                if payment_method == 'MPESA' and saved_sales:
                    reference_tag = f"SALE-{saved_sales[0].id}"
                    mpesa_response = trigger_stk_push(
                        phone=customer_phone,
                        amount=total_order_revenue,
                        reference=reference_tag
                    )

                    if mpesa_response.get('ResponseCode') == '0':
                        checkout_id = mpesa_response.get('CheckoutRequestID')
                        # Attach the same CheckoutRequestID to all items in this batch
                        for sale in saved_sales:
                            sale.mpesa_checkout_id = checkout_id
                            sale.save()

                        return JsonResponse({
                            'status': 'initiated',
                            'transaction_id': saved_sales[0].id,
                            'message': 'STK Push prompted successfully!'
                        })
                    else:
                        error_desc = mpesa_response.get('ResponseDescription', 'Gateway rejection')
                        return JsonResponse(
                            {'status': 'error', 'message': f"M-Pesa push failed: {error_desc}"},
                            status=400
                        )

                # -------------------------------------------------------------------
                # Cash or Credit – immediate success
                # -------------------------------------------------------------------
                return JsonResponse({
                    'status': 'success',
                    'message': f'{len(saved_sales)} items saved successfully.'
                })

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

        # Non‑AJAX POST (shouldn't happen with our frontend)
        else:
            messages.error(request, "Invalid request format.")
            return redirect('record_sale')

    # GET request – show the dashboard with an empty form
    else:
        from .forms import ProductSaleForm   # import locally if needed
        form = ProductSaleForm()

    return _render_sales_dashboard(request, form)
# views.py
def get_product_price(request):
    product_type = request.GET.get('product')
    shop_item_id = request.GET.get('shop_item')
    price = None

    if product_type:
        if product_type == 'OTHER' and shop_item_id:
            try:
                item = ShopItem.objects.get(id=shop_item_id)
                price = item.default_selling_price
            except ShopItem.DoesNotExist:
                pass
        else:
            try:
                stock = ProductStock.objects.get(product_type=product_type)
                price = stock.selling_price
            except ProductStock.DoesNotExist:
                pass

    if price is not None:
        return JsonResponse({'price': str(price)})
    return JsonResponse({'price': None})
# views.py

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from decimal import Decimal
from .models import ProductStock, ShopItem

# @staff_member_required   # only staff (superadmin) can access
def manage_prices(request):
    # Handle POST: save prices
    if request.method == 'POST':
        # Update ProductStock prices
        for key, value in request.POST.items():
            if key.startswith('prod_'):
                pk = key.split('_')[1]
                try:
                    stock = ProductStock.objects.get(pk=pk)
                    stock.selling_price = Decimal(value)
                    stock.save()
                except (ProductStock.DoesNotExist, ValueError):
                    pass
            elif key.startswith('shop_'):
                pk = key.split('_')[1]
                try:
                    item = ShopItem.objects.get(pk=pk)
                    item.default_selling_price = Decimal(value)
                    item.save()
                except (ShopItem.DoesNotExist, ValueError):
                    pass
        messages.success(request, "All prices updated successfully.")
        return redirect('manage_prices')

    # GET: fetch all products
    products = []

    # Milled products
    for stock in ProductStock.objects.all().order_by('product_type'):
        products.append({
            'type': 'Milled',
            'name': stock.get_product_type_display(),
            'price': stock.selling_price,
            'field_id': f'prod_{stock.pk}',
            'pk': stock.pk,
            'model': 'ProductStock'
        })

    # General shop items
    for item in ShopItem.objects.all().order_by('name'):
        products.append({
            'type': 'Shop Item',
            'name': item.name,
            'price': item.default_selling_price,
            'field_id': f'shop_{item.pk}',
            'pk': item.pk,
            'model': 'ShopItem'
        })

    context = {
        'products': products,
        'title': 'Manage Selling Prices',
    }
    return render(request, 'manage_prices.html', context)
# def record_sale(request):
#     """View to handle multi-item cart sales, storing clean data, and handling bale conversions"""
#     if request.method == "POST":
#         # Check if the submission is incoming as JSON (from our new JS cart)
#         if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             try:
#                 data = json.loads(request.body)
#                 cart_items = data.get('items', [])
#                 payment_method = data.get('payment_method', 'CASH')
#                 customer_phone = data.get('customer_phone')
#                 customer_name = data.get('customer_name')

#                 if not cart_items:
#                     return JsonResponse({'status': 'error', 'message': 'Your cart is completely empty.'}, status=400)

#                 if payment_method == 'MPESA' and not customer_phone:
#                     return JsonResponse({'status': 'error', 'message': 'Mobile phone number is required for M-Pesa STK push.'}, status=400)

#                 total_order_revenue = Decimal('0.00')
#                 saved_sales = []

#                 with transaction.atomic():
#                     # 1. PROCESS EACH ITEM IN THE CART
#                     for item in cart_items:
#                         # Instantiate your model manually or via your model form equivalent
#                         # For simplicity and consistency with your original architecture, we save directly to the model instance:
#                         # assumed schema matching your form fields: product, shop_item_id, quantity, selling_price
                        
#                         # Note: If shop_item is present, it's passed as an ID from frontend
#                         shop_item_id = item.get('shop_item')
                        
#                         # Create an unsaved instance of your Sale model
#                         # Replacing form.save(commit=False) structure:
#                         from .models import ProductSale # Adjust import based on your app name
#                         sale = ProductSale()
#                         sale.product = item.get('product')
#                         if shop_item_id and sale.product == 'OTHER':
#                             sale.shop_item_id = int(shop_item_id)
                        
#                         kg_quantity = Decimal(str(item.get('quantity', 0)))
#                         kg_price = Decimal(str(item.get('selling_price', 0)))
                        
#                         # Compute row item revenue manually
#                         sale.total_revenue = (kg_quantity * kg_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#                         total_order_revenue += sale.total_revenue
                        
#                         sale.quantity = kg_quantity
#                         sale.selling_price = kg_price

#                         # Assign Customer names for Credit contexts
#                         if payment_method == 'CREDIT':
#                             sale.payment_status = 'CREDIT'
#                             sale.payment_method = 'CREDIT'
#                             # sale.customer_name = customer_name  # Adjust based on your model layout
#                         elif payment_method == 'MPESA':
#                             sale.payment_status = 'PENDING'
#                             sale.payment_method = 'MPESA'
#                         else:
#                             sale.payment_status = 'PAID'
#                             sale.payment_method = 'CASH'

#                         sale.save()
#                         saved_sales.append(sale)

#                 # 2. SAFARICOM STK PUSH GATEWAY ROUTING
#                 if payment_method == 'MPESA' and saved_sales:
#                     # Anchor the transaction reference tracking to the first sale element ID or an aggregated tag
#                     reference_tag = f"SALE-{saved_sales[0].id}" 
#                     mpesa_response = trigger_stk_push(
#                         phone=customer_phone, 
#                         amount=total_order_revenue,  # Push total cart amount
#                         reference=reference_tag
#                     )
                    
#                     if mpesa_response.get('ResponseCode') == '0':
#                         checkout_id = mpesa_response.get('CheckoutRequestID')
#                         # Update all items under this specific batch push
#                         for sale in saved_sales:
#                             sale.mpesa_checkout_id = checkout_id
#                             sale.save()
                        
#                         return JsonResponse({
#                             'status': 'initiated',
#                             'transaction_id': saved_sales[0].id, # Poll using primary sale asset
#                             'message': 'STK Push prompted successfully!'
#                         })
#                     else:
#                         error_desc = mpesa_response.get('ResponseDescription', 'Gateway rejection')
#                         return JsonResponse({'status': 'error', 'message': f"M-Pesa push initialization failed: {error_desc}"}, status=400)

#                 return JsonResponse({'status': 'success', 'message': f'{len(saved_sales)} items saved successfully.'})

#             except Exception as e:
#                 return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
#         else:
#             messages.error(request, "Invalid non-AJAX structural operational data mode.")
#             return redirect('record_sale')

#     else:
#         form = ProductSaleForm()

#     return _render_sales_dashboard(request, form)
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ProductSale

@csrf_exempt
def mpesa_callback(request):
    """Callback listener that receives payment notices directly from Safaricom"""
    if request.method == 'POST':
        try:
            mpesa_data = json.loads(request.body)
            stk_callback = mpesa_data['Body']['stkCallback']
            result_code = stk_callback['ResultCode']
            checkout_request_id = stk_callback['CheckoutRequestID']
            
            # Find the specific row that contains this unique CheckoutID string
            sale = ProductSale.objects.filter(mpesa_checkout_id=checkout_request_id).first()
            
            if sale:
                if result_code == 0:
                    # Payment Success: Transition the status to PAID
                    sale.payment_status = 'PAID'
                    
                    # Extract receipt number safely if present
                    callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                    for item in callback_metadata:
                        if item['Name'] == 'MpesaReceiptNumber':
                            # If you decide to track the specific receipt token inside your database
                            pass 
                    
                    sale.save()
                    print(f"Sale ID {sale.id} updated successfully to PAID via callback validation.")
                else:
                    # User cancelled, timed out, or entered an incorrect PIN
                    sale.payment_status = 'PENDING'  # Or 'FAILED' depending on design choices
                    sale.save()
                    print(f"Transaction failed for Sale ID {sale.id} with code {result_code}")
                    
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})
            
        except Exception as e:
            print(f"Callback processing fatal exception: {str(e)}")
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Internal Server Error"})
            
    return HttpResponse("Invalid request method", status=405)
# def _render_sales_dashboard(request, form):
#     """Helper function to keep dashboard aggregation metrics DRY"""
#     recent_sales = ProductSale.objects.all().order_by('-sold_at')[:10]
    
#     paid_total = ProductSale.objects.filter(
#         Q(payment_status='PAID') | Q(payment_status='COMPLETED')
#     ).aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0
    
#     credit_total = ProductSale.objects.filter(
#         payment_status='CREDIT'
#     ).aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0

#     return render(request, 'sales.html', {
#         'form': form, 
#         'paid_total': paid_total, 
#         'credit_total': credit_total, 
#         'recent_sales': recent_sales,
#     })

# Ensure you have a view for the JS to check status
def check_mpesa_status(request, transaction_id):
    try:
        sale = ProductSale.objects.get(id=transaction_id)
        return JsonResponse({'payment_status': sale.payment_status})
    except ProductSale.DoesNotExist:
        return JsonResponse({'payment_status': 'NOT_FOUND'}, status=404)


def milk_margin(request):
    pass
def Admin_collect_milk(request):
    if request.method == 'POST':
        form = MilkCollectionForm(request.POST)
        if form.is_valid():
            try:
                # 1. We ONLY call form.save(). 
                # The Model's save() method will handle stock, balance, and collection_no.
                with transaction.atomic():
                    collection = form.save()
                    
                    # 2. Prepare SMS using data from the saved collection
                    farmer = collection.farmer
                    clean_phone = str(farmer.phone_number).replace('+', '').replace(' ', '')
                    if clean_phone.startswith('0'):
                        clean_phone = '254' + clean_phone[1:]
                        
                    # Use 'total_cost' (from your model) instead of 'total_payout'
                    msg = f"Hello {farmer.name}, collected {collection.litres}L. Payout: KES {collection.total_cost}. Ref: {collection.collection_no}"
                    
                    # 3. Send SMS
                    send_infobip_sms(clean_phone, msg)

                messages.success(request, "Collection recorded and SMS sent!")
                return redirect('Admin')
                
            except Exception as e:
                # This catches the error and displays it on your page
                messages.error(request, f"Database Error: {str(e)}")
    else:
        form = MilkCollectionForm()
    
    return render(request, 'Admin_milk_collection.html', {'form': form})
            
                    
# def collect_milk(request):
#     if request.method == "POST":
#         form = MilkCollectionForm(request.POST)
#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     # 1. Save collection (Farmer balance updated in model save() logic)
#                     collection = form.save()
                    
#                     # 2. Update Inventory Stock (The Shop Shelf)
#                     stock, _ = ProductStock.objects.get_or_create(product_type='MILK')
#                     stock.quantity += collection.litres
#                     stock.save()

#                     farmer = collection.farmer

#                 # --- SMS SENDING ---
#                 # Strip '+' for Infobip API
#                 clean_phone = str(farmer.phone_number).replace('+', '')
#                 msg = (f"Hello {farmer.name}, collected {collection.litres}L at Ksh {collection.buying_price}/L. "
#                        f"Total: Ksh {collection.total_cost}. Your milk balance is Ksh {farmer.milking_balance}")
                
#                 send_infobip_sms(clean_phone, msg)

#                 messages.success(request, "Milk collection recorded and SMS sent!")
#                 return redirect('manager_dashboard') 
            
#             except Exception as e:
#                 messages.error(request, f"Failed to record collection: {str(e)}")
        
#     else:
#         form = MilkCollectionForm()
        
#     return render(request, 'milk_collection.html', {'form': form})
from decimal import Decimal
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect, render

def collect_milk(request):
    if request.method == "POST":
        form = MilkCollectionForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():

                    # 1. SAVE ONLY
                    collection = form.save()

                    # 2. UPDATE STOCK (ONLY HERE)
                    stock, _ = ProductStock.objects.select_for_update().get_or_create(
                        product_type='MILK'
                    )

                    stock.quantity += Decimal(str(collection.litres))
                    stock.save()

                    # 3. UPDATE FARMER BALANCE (ONLY HERE NOW)
                    farmer = collection.farmer
                    farmer.milking_balance += Decimal(str(collection.total_cost))
                    farmer.save()

                    # 4. SMS
                    clean_phone = str(farmer.phone_number).replace('+', '')

                    msg = (
                        f"Hello {farmer.name}, "
                        f"Collected {collection.litres}L. "
                        f"Total Ksh {collection.total_cost}. "
                        f"Balance Ksh {farmer.milking_balance}"
                    )

                    send_infobip_sms(clean_phone, msg)

                    messages.success(request, "Milk collection recorded successfully!")
                    return redirect('manager_dashboard')

            except Exception as e:
                messages.error(request, f"Failed: {str(e)}")

    else:
        form = MilkCollectionForm()

    return render(request, 'milk_collection.html', {'form': form})
def farmer_listy(request):
    # Fetch all farmers and their related counts/balances
    farmers = Farmer.objects.all().order_by('-joined_date')
    
    return render(request, 'farmer_list.html', {'farmers': farmers})
def farmer_list(request):

    farmers = Farmer.objects.annotate(
        total_maize=Sum('maize_deliveries__sacks_delivered'),
        total_milk=Sum('milkcollection__litres'),
        total_balance=F('milling_balance') + F('milking_balance')
    ).order_by('-joined_date')

    return render(request, 'farmers_list.html', {
        'farmers': farmers
    })


def farmer_detail(request, farmer_id):
    farmer = get_object_or_404(Farmer, farmer_id=farmer_id)
    
    # Get all history for this specific farmer
    maize_history = MaizeIntake.objects.filter(farmer=farmer).order_by('-date')
    milk_history = MilkCollection.objects.filter(farmer=farmer).order_by('-date')
    payment_history = FarmerPayment.objects.filter(farmer=farmer).order_by('-date')
    
    context = {
        'farmer': farmer,
        'maize_history': maize_history,
        'milk_history': milk_history,
        'payments': payment_history,
        'total_balance': farmer.milling_balance + farmer.milking_balance
    }
    return render(request, 'farmer_detail.html', context)


def manage_farmer_full(request, pk):
    farmer = get_object_or_404(Farmer, pk=pk)
    maize_records = farmer.maize_deliveries.all().order_by('-date')
    milk_records = MilkCollection.objects.filter(farmer=farmer).order_by('-date')
    
    if request.method == "POST":
        # Check which form was submitted
        if 'update_farmer' in request.POST:
            form = FarmerForm(request.POST, instance=farmer)
            if form.is_valid():
                form.save()
                messages.success(request, f"Details for {farmer.name} updated.")
                return redirect('manage_farmer_full', pk=pk)
        
        # Add logic here if you want to delete or edit specific row IDs
        # via a different POST action
                
    else:
        form = FarmerForm(instance=farmer)

    context = {
        'farmer': farmer,
        'form': form,
        'maize_records': maize_records,
        'milk_records': milk_records,
    }
    return render(request, 'manage_farmer.html', context)

def edit_milk(request, record_id):
    # 1. Get the specific record
    record = get_object_or_404(MilkCollection, pk=record_id)
    old_total = record.total_cost  # The amount before editing
    farmer = record.farmer

    if request.method == "POST":
        form = MilkCollectionForm(request.POST, instance=record)
        if form.is_valid():
            with transaction.atomic():
                # Save the new details
                updated_record = form.save()
                
                # Adjust Farmer Balance: Remove old amount, add new amount
                farmer.milking_balance = (farmer.milking_balance - old_total) + updated_record.total_cost
                farmer.save()
                
                messages.success(request, f"Milk record for {farmer.name} updated successfully.")
                return redirect('manage_farmer_full', pk=farmer.pk)
    else:
        form = MilkCollectionForm(instance=record)
    
    return render(request, 'edit_record_generic.html', {
        'form': form, 
        'title': f'Edit Milk Record: {record.date}',
        'farmer': farmer
    })
def delete_milk(request, record_id):
    record = get_object_or_404(MilkCollection, pk=record_id)
    farmer = record.farmer
    amount_to_deduct = record.total_cost

    try:
        with transaction.atomic():
            # 1. Deduct the amount from the farmer's balance
            farmer.milking_balance -= amount_to_deduct
            farmer.save()
            
            # 2. Delete the record
            record.delete()
            
            messages.warning(request, f"Record deleted. KES {amount_to_deduct} was deducted from {farmer.name}'s balance.")
    except Exception as e:
        messages.error(request, f"Error deleting record: {e}")

    return redirect('manage_farmer_full', pk=farmer.pk)


def edit_maize(request, record_id):
    # 1. Get the record and the farmer
    record = get_object_or_404(MaizeIntake, pk=record_id)
    old_credit = record.total_credit  # Store the original value
    farmer = record.farmer

    if request.method == "POST":
        form = MaizeIntakeForm(request.POST, instance=record)
        if form.is_valid():
            with transaction.atomic():
                # Save new data
                updated_record = form.save()
                
                # Adjust Balance: Subtract the old amount and add the new amount
                farmer.milling_balance = (farmer.milling_balance - old_credit) + updated_record.total_credit
                farmer.save()
                
                messages.success(request, f"Maize delivery for {farmer.name} updated.")
                return redirect('manage_farmer_full', pk=farmer.pk)
    else:
        form = MaizeIntakeForm(instance=record)
    
    return render(request, 'edit_record_generic.html', {
        'form': form, 
        'title': 'Edit Maize Intake',
        'farmer': farmer
    })

def delete_maize(request, record_id):
    record = get_object_or_404(MaizeIntake, pk=record_id)
    farmer = record.farmer
    amount_to_remove = record.total_credit

    with transaction.atomic():
        # 1. Deduct the value from the farmer's balance
        farmer.milling_balance -= amount_to_remove
        farmer.save()
        
        # 2. Remove the record
        record.delete()
        
        messages.warning(request, f"Maize record deleted. KES {amount_to_remove} removed from balance.")

    return redirect('manage_farmer_full', pk=farmer.pk)
from django.shortcuts import render, get_object_or_404
from .models import MaizeIntake, MilkCollection

def generate_receipt(request, type, pk):
    if type == 'maize':
        record = get_object_or_404(MaizeIntake, pk=pk)
        title = "Maize Delivery Receipt"
        # Map fields to a common name for the template
        data = {
            'qty': record.sacks_delivered,
            'unit': 'Sacks',
            'price': record.price_per_sack,
            'total': record.total_credit,
            'id': record.intake_no
        }
    else:
        record = get_object_or_404(MilkCollection, pk=pk)
        title = "Milk Collection Receipt"
        data = {
            'qty': record.litres,
            'unit': 'Litres',
            'price': record.buying_price,
            'total': record.total_cost,
            'id': f"MLK-{record.id}"
        }

    return render(request, 'receipt_print.html', {
        'record': record,
        'title': title,
        'data': data
    })


def business_report(request):
    # --- 1. MILK REPORT ---
    milk_collections = MilkCollection.objects.all()
    milk_sales = ProductSale.objects.filter(product='MILK')
    
    avg_milk_buying_price = milk_collections.aggregate(Avg('buying_price'))['buying_price__avg'] or 0
    avg_milk_selling_price = milk_sales.aggregate(Avg('selling_price'))['selling_price__avg'] or 0
    total_milk_litres_sold = milk_sales.aggregate(Sum('quantity'))['quantity__sum'] or 0
    
    milk_margin_per_litre = avg_milk_selling_price - avg_milk_buying_price
    total_milk_profit = milk_margin_per_litre * total_milk_litres_sold

    # --- 2. MAIZE & SHOP REPORT (Flour, Germ, Bran) ---
    # We calculate the cost of one sack of maize vs what the resulting products sold for
    maize_intake = MaizeIntake.objects.all()
    avg_maize_cost_per_sack = maize_intake.aggregate(Avg('price_per_sack'))['price_per_sack__avg'] or 0
    
    # Shop Sales
    shop_products = ['FLOUR', 'GERM', 'BRAN']
    shop_reports = []
    
    for prod_code in shop_products:
        sales = ProductSale.objects.filter(product=prod_code)
        total_qty = sales.aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_rev = sales.aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0
        avg_sell = sales.aggregate(Avg('selling_price'))['selling_price__avg'] or 0
        
        shop_reports.append({
            'name': prod_code,
            'quantity_sold': total_qty,
            'revenue': total_rev,
            'avg_selling_price': avg_sell,
        })

    context = {
        'milk_report': {
            'avg_buy': avg_milk_buying_price,
            'avg_sell': avg_milk_selling_price,
            'margin': milk_margin_per_litre,
            'total_profit': total_milk_profit,
            'total_qty': total_milk_litres_sold
        },
        'shop_reports': shop_reports,
        'avg_maize_cost': avg_maize_cost_per_sack
    }
    return render(request, 'business_summary.html', context)

def full_farmer_report(request, farmer_id):
    farmer = get_object_or_404(Farmer, farmer_id=farmer_id)
    
    # --- MILK SECTION ---
    # Order by date so the "Day Milk was Recorded" makes sense
    milk_collections = MilkCollection.objects.filter(farmer=farmer).order_by('-date')
    total_milk_litres = milk_collections.aggregate(Sum('litres'))['litres__sum'] or 0
    total_milk_cost = milk_collections.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
    
    avg_milk_sell = ProductSale.objects.filter(product='MILK').aggregate(Avg('selling_price'))['selling_price__avg'] or 0
    estimated_milk_revenue = total_milk_litres * avg_milk_sell
    milk_margin = estimated_milk_revenue - total_milk_cost

    # --- MAIZE SECTION ---
    maize_deliveries = MaizeIntake.objects.filter(farmer=farmer).order_by('-date')
    total_sacks = maize_deliveries.aggregate(Sum('sacks_delivered'))['sacks_delivered__sum'] or 0
    total_maize_cost = maize_deliveries.aggregate(Sum('total_credit'))['total_credit__sum'] or 0
    
    avg_flour_price = ProductSale.objects.filter(product='FLOUR').aggregate(Avg('selling_price'))['selling_price__avg'] or 0
    est_bales = Decimal(total_sacks) * Decimal('2.5')
    estimated_maize_revenue = est_bales * avg_flour_price
    maize_margin = estimated_maize_revenue - total_maize_cost

    # --- PAYMENT HISTORY ---
    # Fetching actual money paid out to the farmer
    payments = FarmerPayment.objects.filter(farmer=farmer).order_by('-date')
    total_amount_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'farmer': farmer,
        'milk': {
            'records': milk_collections,
            'total_qty': total_milk_litres,
            'total_cost': total_milk_cost,
            'margin': milk_margin,
        },
        'maize': {
            'records': maize_deliveries,
            'total_qty': total_sacks,
            'total_cost': total_maize_cost,
            'revenue': estimated_maize_revenue,
        },
        'payments': {
            'records': payments,
            'total_paid': total_amount_paid,
        },
        'grand_total_owed': (farmer.milling_balance + farmer.milking_balance) - total_amount_paid
    }
    return render(request, 'full_farmer_statement.html', context)

def payment_dashboard(request):
    # 1. FARMER PAYOUT STATUS (Buying)
    farmers = Farmer.objects.all()
    total_owed_to_farmers = farmers.aggregate(
        total=Sum('milking_balance') + Sum('milling_balance')
    )['total'] or 0
    
    # Identify cleared vs pending farmers
    cleared_farmers = farmers.filter(milking_balance=0, milling_balance=0).count()
    pending_farmers = farmers.filter(Q(milking_balance__gt=0) | Q(milling_balance__gt=0)).count()

    # 2. SHOP SALES STATUS (Selling)
    sales = ProductSale.objects.all()
    actual_cash_collected = sales.filter(payment_status='PAID').aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0
    total_customer_credit = sales.filter(payment_status='CREDIT').aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0

    # 3. RECENT SETTLEMENTS
    recent_payouts = FarmerPayment.objects.select_related('farmer').order_by('-date')[:10]

    context = {
        'total_owed': total_owed_to_farmers,
        'cleared_farmers': cleared_farmers,
        'pending_farmers': pending_farmers,
        'cash_in_hand': actual_cash_collected,
        'customer_debt': total_customer_credit,
        'recent_payouts': recent_payouts,
        # Business Health Check
        'net_position': actual_cash_collected - total_owed_to_farmers
    }
    
    return render(request, 'payment_status.html', context)

def pay_farmer(request, farmer_id):
    farmer = get_object_or_404(Farmer, id=farmer_id)
    total_due = farmer.milking_balance + farmer.milling_balance

    if request.method == "POST":
        amount = Decimal(request.POST.get('amount', 0))
        category = request.POST.get('category') 
        method = request.POST.get('method') # 'CASH' or 'MPESA'
        ref = request.POST.get('reference')

        if amount <= 0:
            messages.error(request, "Invalid amount.")
        elif (category == 'MILK' and amount > farmer.milking_balance) or \
             (category == 'MAIZE' and amount > farmer.milling_balance):
            messages.error(request, "Amount exceeds balance.")
        else:
            with transaction.atomic():
                # 1. Create the local payment record
                payment = FarmerPayment.objects.create(
                    farmer=farmer,
                    category=category,
                    amount=amount,
                    reference=ref if method == 'CASH' else f"PENDING-{uuid.uuid4().hex[:4]}"
                )
                
                if method == 'MPESA':
                    # Trigger B2C (Business to Customer) API here
                    # mpesa_response = trigger_b2c_payout(farmer.phone_number, amount)
                    messages.info(request, f"M-Pesa Payout initiated for {farmer.name}.")
                else:
                    messages.success(request, f"Manual Cash payment of KES {amount} recorded.")
                
                return redirect('payment_dashboard')

    return render(request, 'pay_farmer.html', {'farmer': farmer, 'total_due': total_due})
def paym_receipt(request, payment_id):
    payment = get_object_or_404(FarmerPayment, id=payment_id)
    return render(request, 'farmer_receipt.html', {'payment': payment})
def general_milk_margin_report(request):
    # 1. Pull records exactly as they are in the DB
    all_collections = MilkCollection.objects.all().order_by('-date')
    
    # 2. Hardcode your actual target Shop Price
    shop_price = Decimal('60.00') 

    for record in all_collections:
        # Pull buying price directly from the 'price_per_litre' field in DB
        buying_price = Decimal(record.buying_price)
        
        # Calculate margin based on actual DB figures
        # Profit = (60 - Actual price paid to farmer) * Litres
        record.calculated_margin = (shop_price - buying_price) * Decimal(record.litres)

    # 3. Totals (Summing the actual DB columns)
    total_qty = all_collections.aggregate(Sum('litres'))['litres__sum'] or 0
    total_cost = all_collections.aggregate(Sum('total_cost'))['total_cost __sum'] or 0
    
    # Financial result
    total_revenue = Decimal(total_qty) * shop_price
    total_margin = total_revenue - Decimal(total_cost)

    context = {
        'records': all_collections,
        'shop_price': shop_price,
        'total_qty': total_qty,
        'total_cost': total_cost,
        'total_revenue': total_revenue,
        'total_margin': total_margin,
    }
    return render(request, 'general_milk_report.html', context)
from datetime import datetime, time
def report(request):
    # 1. Get dates from user or default to today
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Convert strings to actual date objects
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.combine(datetime.strptime(end_date_str, '%Y-%m-%d'), time.max)
    else:
        # Default to showing everything for the current month
        start_date = timezone.now().replace(day=1, hour=0, minute=0)
        end_date = timezone.now()

    # 2. MILK DATA
    milk_data = MilkCollection.objects.filter(date__range=[start_date, end_date])
    total_milk_litres = milk_data.aggregate(Sum('litres'))['litres__sum'] or 0
    total_milk_cost = milk_data.aggregate(Sum('total_cost'))['total_cost__sum'] or 0

    # 3. MAIZE/MILLING DATA
    maize_intake = MaizeIntake.objects.filter(date__range=[start_date, end_date])
    total_sacks_received = maize_intake.aggregate(Sum('sacks_delivered'))['sacks_delivered__sum'] or 0
    
    milling_batches = MillingBatch.objects.filter(date__range=[start_date, end_date])
    sacks_milled = milling_batches.aggregate(Sum('sacks_pulled_from_store'))['sacks_pulled_from_store__sum'] or 0

    # 4. SALES DATA (Revenue)
    sales = ProductSale.objects.filter(sold_at__range=[start_date, end_date])
    
    # Revenue split by product
    milk_revenue = sales.filter(product='MILK').aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0
    milling_revenue = sales.exclude(product='MILK').aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0
    total_revenue = milk_revenue + milling_revenue

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'milk_litres': total_milk_litres,
        'milk_cost': total_milk_cost,
        'milk_revenue': milk_revenue,
        'sacks_received': total_sacks_received,
        'sacks_milled': sacks_milled,
        'milling_revenue': milling_revenue,
        'total_revenue': total_revenue,
    }
    return render(request, 'report.html', context)
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .forms import AddShopItemForm
from .models import ShopItemStock, ShopItem

def add_shop_item(request):
    if request.method == "POST":
        form = AddShopItemForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Save the basic catalog item details
                    shop_item = form.save()
                    
                    # 2. Grab the stock values from the form's cleaned data
                    qty = form.cleaned_data.get('initial_stock', 0.00)
                    reorder = form.cleaned_data.get('reorder_level', 5.00)
                    
                    # 3. Create the linked stock row automatically
                    ShopItemStock.objects.create(
                        item=shop_item,
                        quantity=qty,
                        reorder_level=reorder
                    )
                    
                    messages.success(request, f"Successfully added {shop_item.name} to inventory!")
                    return redirect('add_shop_item') # Or change to your product list view
                    
            except Exception as e:
                messages.error(request, f"Error saving item: {str(e)}")
    else:
        form = AddShopItemForm()
        
    # Fetch existing items to display them as a list on the same page
    all_items = ShopItem.objects.all().select_related('stock').order_by('-created_at')
    
    return render(request, 'add_shop_item.html', {
        'form': form,
        'all_items': all_items
    })
from django.shortcuts import render
from django.db.models import F, ExpressionWrapper, DecimalField
from decimal import Decimal
from .models import MilkCollection, MaizeIntake, ProductSale, MillingBatch
from django.shortcuts import render
from django.db.models import F, ExpressionWrapper, DecimalField
from django.utils.dateparse import parse_date
from decimal import Decimal
import datetime
from .models import MilkCollection, MaizeIntake, ProductSale, MillingBatch

def business_margin_report(request):
    # Get date filters from request GET parameters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None

    # Base Querysets
    milk_records = MilkCollection.objects.all().select_related('farmer')
    milling_batches = MillingBatch.objects.all().order_by('-date')
    shop_sales = ProductSale.objects.filter(product='OTHER').select_related('shop_item')

    # Apply date filters if provided
    if start_date and end_date:
        # Make the end_date inclusive of the entire day (up to 23:59:59)
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
        
        milk_records = milk_records.filter(date__range=(start_date, end_datetime))
        milling_batches = milling_batches.filter(date__range=(start_date, end_datetime))
        shop_sales = shop_sales.filter(sold_at__range=(start_date, end_datetime))

    # ----------------------------------------------------
    # 1. FARMER MILK REPORT PROCESSING
    # ----------------------------------------------------
    milk_records = milk_records.annotate(
        unit_margin=ExpressionWrapper(F('selling_price') - F('buying_price'), output_field=DecimalField()),
        total_margin=ExpressionWrapper((F('selling_price') - F('buying_price')) * F('litres'), output_field=DecimalField())
    )

    # ----------------------------------------------------
    # 2. MAIZE MILLING MARGINS PROCESSING
    # ----------------------------------------------------
    price_flour1 = ProductSale.objects.filter(product='FLOUR1').order_by('-sold_at').values_list('selling_price', flat=True).first() or Decimal('0.00')
    price_flour2 = ProductSale.objects.filter(product='FLOUR2').order_by('-sold_at').values_list('selling_price', flat=True).first() or Decimal('0.00')
    price_germ = ProductSale.objects.filter(product='GERM').order_by('-sold_at').values_list('selling_price', flat=True).first() or Decimal('0.00')
    price_bran = ProductSale.objects.filter(product='BRAN').order_by('-sold_at').values_list('selling_price', flat=True).first() or Decimal('0.00')

    avg_buying_price_per_sack = MaizeIntake.objects.all().order_by('-date').values_list('price_per_sack', flat=True).first() or Decimal('0.00')

    maize_milling_data = []
    for batch in milling_batches:
        if batch.sacks_pulled_from_store <= 0:
            continue
            
        revenue_flour1 = batch.one_kg_flour_bales * price_flour1
        revenue_flour2 = batch.two_kg_flour_bales * price_flour2
        revenue_germ = batch.maize_germ_kg * price_germ
        revenue_bran = batch.maize_bran_kg * price_bran
        
        total_batch_revenue = revenue_flour1 + revenue_flour2 + revenue_germ + revenue_bran
        total_batch_cost = batch.sacks_pulled_from_store * avg_buying_price_per_sack
        batch_margin = total_batch_revenue - total_batch_cost
        
        estimated_revenue_per_sack = total_batch_revenue / batch.sacks_pulled_from_store
        margin_per_sack = estimated_revenue_per_sack - avg_buying_price_per_sack

        maize_milling_data.append({
            "batch_no": batch.batch_no,
            "sacks_processed": batch.sacks_pulled_from_store,
            "buying_price_per_sack": avg_buying_price_per_sack,
            "estimated_yield_revenue_per_sack": estimated_revenue_per_sack,
            "margin_per_sack": margin_per_sack,
            "total_batch_margin": batch_margin,
            "date_recorded": batch.date
        })

    # ----------------------------------------------------
    # 3. GENERAL SHOP REPORT PROCESSING
    # ----------------------------------------------------
    shop_sales = shop_sales.annotate(
        item_buying_price=F('shop_item__buying_price'),
        unit_margin=ExpressionWrapper(F('selling_price') - F('shop_item__buying_price'), output_field=DecimalField()),
        total_margin=ExpressionWrapper((F('selling_price') - F('shop_item__buying_price')) * F('quantity'), output_field=DecimalField())
    )

    context = {
        "milk_collections": milk_records,
        "maize_batches": maize_milling_data,
        "shop_sales": shop_sales,
        "start_date": start_date_str,
        "end_date": end_date_str,
    }
    
    return render(request, 'margin_report.html', context)