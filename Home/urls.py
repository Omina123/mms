from django.contrib import admin
from django.urls import path
from Home.views import *

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('about/', About, name='about'),
    path('services/', Services, name='services'),  
      path('Contact/', Contact, name='Contact'),
      path('Admin/', Admin, name='Admin'),
      path('manager_dashboard/', manager_dashboard, name='manager_dashboard'),
      path('add_farmers/', add_farmer, name='add_farmers'),
      path('record_maize_intake/', record_maize_intake, name='record_maize_intake'),
      path('intake-history/', maize_intake_list, name='maize_intake_list'),
      path('process_milling_batch/', process_milling_batch, name='process_milling_batch'),
      path ('record_sale/', record_sale, name='record_sale'),
      path('collect_milk/', collect_milk, name='collect_milk'),
      path('farmer_list/', farmer_list, name='farmer_list'),
     path('farmer_detail/<str:farmer_id>/', farmer_detail, name='farmer_detail'),
     path('edit_milk/<int:record_id>/', edit_milk, name='edit_milk'),
     # In your urls.py
    path('manage_farmer_full/<int:pk>/', manage_farmer_full, name='manage_farmer_full'),
     path('farmer_listy',farmer_listy, name='farmer_listy'),
    #  path('edit_milk/<int:pk>/', edit_milk, name='edit_milk'),
path('delete_milk/<int:record_id>/', delete_milk, name='delete_milk'),
path('edit_maize/<int:record_id>/', edit_maize, name='edit_maize'),
path('delete_maize/<int:record_id>/', delete_maize, name='delete_maize'),
path('receipt/<str:type>/<int:pk>/', generate_receipt, name='generate_receipt'),
path('pay_farmer/<int:farmer_id>/', pay_farmer, name='pay_farmer'),
path('business_report/', business_report, name='business_report'),
path('full_farmer_report/<str:farmer_id>/', full_farmer_report, name='full_farmer_report'),
path('payment_dashboard/', payment_dashboard, name='payment_dashboard'),
path('paym_receipt/<int:payment_id>/', paym_receipt, name='paym_receipt'),
# urls.py
path('mpesa/callback/', mpesa_callback, name='mpesa_callback'),path('check-mpesa-status/<int:transaction_id>/', check_mpesa_status, name='check_status'),

    path('print_receipt/<str:sale_id>/', print_receipt, name='print_receipt'),
    path('general_milk_margin_report/', general_milk_margin_report, name='general_milk_margin_report'),
    path ('sales_report/', sales_report, name='sales_report'),
    path('report/', report, name='report'),
    path ('Admin_maize_intake_list/', Admin_maize_intake_list, name='Admin_maize_intake_list'),
    path('Admin_record_maize_intake/', Admin_record_maize_intake, name='Admin_record_maize_intake'),
    path('Admin_collect_milk/', Admin_collect_milk, name='Admin_collect_milk'),
]