import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64
from django.conf import settings

def get_mpesa_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    
    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    return r.json()['access_token']

def trigger_stk_push(phone, amount, reference):
    # Safety check: if amount is None, default to 0 to avoid int() error
    if amount is None:
        amount = 0
        
    access_token = get_mpesa_access_token()
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    formatted_phone = "254" + str(phone)[-9:]
    
    shortcode = "174379" 
    passkey = settings.MPESA_PASSKEY 
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    data_to_encode = shortcode + passkey + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode()

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(float(amount)), # Convert float/string to int safely
        "PartyA": formatted_phone,
        "PartyB": shortcode,
        "PhoneNumber": formatted_phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": reference,
        "TransactionDesc": f"Payment for {reference}"
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()