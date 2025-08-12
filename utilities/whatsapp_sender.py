# utilities/whatsapp_sender.py
import requests
from models.setting import Setting
from models.store import Store
from models.customer import Customer
from utilities.localization import get_translation

def send_whatsapp_message(target, message):
    """
    Sends a WhatsApp message using the Fonnte API.
    Retrieves the API token from the database.
    """
    # Retrieve the API token from the settings table in the database
    token = Setting.get_value('whatsapp_api_token')

    if not token:
        print("Error: WhatsApp API token is not set in the database.")
        return {'status': False, 'reason': 'API token not configured.'}

    url = 'https://api.fonnte.com/send'
    
    payload = {
        'target': target,
        'message': message,
        'countryCode': '62'  # Assuming the country code is always Indonesia
    }
    
    headers = {
        'Authorization': token
    }
    
    try:
        # Set a timeout for the request
        response = requests.post(
            url,
            data=payload,
            headers=headers,
            timeout=10
        )
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()
        print(f"WhatsApp message sent successfully to {target}. Response: {response.json()}")
        return response.json()
    except requests.exceptions.Timeout:
        print(f"Error sending message to {target}: Request timed out.")
        return {'status': False, 'reason': 'Request timed out.'}
    except requests.exceptions.HTTPError as e:
        print(f"Error sending message to {target}: HTTP Error - {e.response.status_code} {e.response.text}")
        return {'status': False, 'reason': f"HTTP Error: {e.response.status_code}"}
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to {target}: {e}")
        return {'status': False, 'reason': 'A network error occurred.'}

def format_reservation_message(reservation):
    """
    Formats the reservation details into a user-friendly message.
    """
    try:
        store = Store.find_by_id(reservation.store_id)
        customer = Customer.find_by_id(reservation.customer_id)

        if not store or not customer:
            return None

        # Using translation keys for a multilingual message template
        message = (
            f"*{get_translation('whatsapp.greeting')}*\n\n"
            f"{get_translation('whatsapp.intro')}:\n\n"
            f"*{get_translation('customers.customer_name')}:* {customer.customer_name}\n"
            f"*{get_translation('stores.store_name')}:* {store.store_name}\n"
            f"*{get_translation('reservations.reservation_code')}:* {reservation.reservation_code}\n"
            f"*{get_translation('reservations.reservation_datetime')}:* {reservation.reservation_datetime.strftime('%A, %d %B %Y - %H:%M')}\n"
            f"*{get_translation('reservations.reservation_status')}:* {get_translation('reservation_statuses.' + reservation.reservation_status)}\n"
        )

        # Add optional fields if they exist
        if reservation.reservation_event:
            message += f"*{get_translation('reservations.reservation_event')}:* {reservation.reservation_event}\n"
        if reservation.reservation_room:
            message += f"*{get_translation('reservations.reservation_room')}:* {reservation.reservation_room}\n"
        if reservation.reservation_guests:
            message += f"*{get_translation('reservations.reservation_guests')}:* {reservation.reservation_guests}\n"

        message += f"\n{get_translation('whatsapp.thank_you')}"

        return message
    except Exception as e:
        print(f"Error formatting reservation message: {e}")
        return None