# import ssl
# import africastalking

# # Add this line to force the script to use a safer SSL context
# ssl._create_default_https_context = ssl._create_unverified_context

# # 1. Setup Credentials
# username = "sandbox" 
# api_key = "atsk_da2b3c9ee4a21acaf5038897a040bbac9c0a16fc9107dcdfced30410266f44b9cff334a8"

# # 2. Initialize
# africastalking.initialize(username, api_key)
# sms = africastalking.SMS

# def test_send():
#     # REPLACE with your phone number to see it in the simulator
#     phone = "+254759975197" 
#     batch_id = "402"
#     sacks = "45"
#     unga = "210"
    
#     message = f"Milling Alert: Batch #{batch_id} complete. \nInput: {sacks} Sacks\nOutput: {unga} Unga Bales."
    
#     print("--- Sending SMS ---")
#     try:
#         response = sms.send(message, [phone])
#         print("Success! Response from AT:")
#         print(response)
#     except Exception as e:
#         print(f"Failed! Error: {e}")

# if __name__ == "__main__":
#     test_send()
import os
import certifi
import africastalking

# FIX SSL CERT PATH
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
username = "sandbox"
api_key = "atsk_da2b3c9ee4a21acaf5038897a040bbac9c0a16fc9107dcdfced30410266f44b9cff334a8"

africastalking.initialize(username, api_key)

sms = africastalking.SMS

def test_send():
    phone = "+254759975197"

    message = "Milling Alert: Batch #402 complete."

    try:
        response = sms.send(message, [phone])
        print("Success:", response)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_send()