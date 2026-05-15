import http.client
import json

def send_infobip_sms(to_number, message_text):
    """
    Utility to send SMS via Infobip API.
    Handles number normalization and API request execution.
    """
    # 1. Normalize the phone number for Infobip
    clean_number = str(to_number).replace('+', '').replace(' ', '')
    
    if clean_number.startswith('0'):
        clean_number = '254' + clean_number[1:]

    # 2. Setup Connection
    conn = http.client.HTTPSConnection("pdgddl.api.infobip.com")
    
    # 3. Prepare Payload (Updated to fix the 'content' violation)
    payload = json.dumps({
        "messages": [
            {
                "destinations": [
                    {
                        "to": clean_number
                    }
                ],
                # Changed 'from' to 'sender' and updated to your guide's trial number
                "sender": "447491163443",  
                "content": {
                    "text": message_text
                }
            }
        ]
    })
    
    # 4. Setup Headers with your API Key
    headers = {
        'Authorization': 'App a0c1cc47fd99550669269a1179fcd9d8-6af98bac-171b-4d14-a5e3-1b3ebac4d97e',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # 5. Execute Request
    try:
        conn.request("POST", "/sms/3/messages", payload, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        
        # Log response for debugging
        print(f"--- SMS SENT TO {clean_number} ---")
        print(f"Status: {res.status}")
        print(f"Response: {data}")
        
        return data
    except Exception as e:
        print(f"--- SMS CRITICAL ERROR ---")
        print(f"Error details: {e}")
        return None
    finally:
        conn.close()