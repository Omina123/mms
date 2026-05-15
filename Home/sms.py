import africastalking
from django.conf import settings

# Initialize AT
username = "sandbox" # Change to your live username
api_key = "atsk_da2b3c9ee4a21acaf5038897a040bbac9c0a16fc9107dcdfced30410266f44b9cff334a8"
africastalking.initialize(username, api_key)
sms = africastalking.SMS

def send_milling_status(phone, batch_id, sacks, unga):
    """
    Sends a professional update to the Manager/Client
    Example: "Batch #402 Processed: 45 Sacks -> 210 Unga Bales."
    """
    message = f"Milling Alert: Batch #{batch_id} complete. \nInput: {sacks} Sacks\nOutput: {unga} Unga Bales."
    
    try:
        # Ensure phone starts with +254
        response = sms.send(message, [phone])
        return response
    except Exception as e:
        return str(e)