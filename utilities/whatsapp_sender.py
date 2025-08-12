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
            f"*{get_translation('customers.customer_name')}:* {customer.customer_name}\n"
            f"*{get_translation('common.telephone')}:* {customer.customer_telephone}\n"
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
        if reservation.reservation_guests:
            message += f"*{get_translation('reservations.reservation_notes')}:* {reservation.reservation_notes}\n"

        message += f"\n{get_translation('whatsapp.thank_you')}"

        return message
    except Exception as e:
        print(f"Error formatting reservation message: {e}")
        return None

# --- NEW: Function to format Revenue report ---
def format_revenue_message(revenue, revenue_items, revenue_compliments):
    """
    Formats the revenue details into a user-friendly WhatsApp message.
    """
    try:
        store = revenue.get_store_details()
        if not store:
            return None

        # Calculate totals
        total_additions = sum(item.revenue_item_amount for item in revenue_items if item.get_revenue_type_category() == 'Addition')
        total_deductions = sum(item.revenue_item_amount for item in revenue_items if item.get_revenue_type_category() == 'Deduction')
        net_revenue = total_additions - total_deductions

        # --- Message Header ---
        message = (
            f"*{get_translation('whatsapp.revenue_report_title')}*\n\n"
            f"*{get_translation('stores.store_name')}:* {store.store_name}\n"
            f"*{get_translation('revenues.revenue_date')}:* {revenue.revenue_date.strftime('%d %B %Y')}\n"
            f"*{get_translation('revenues.guests')}:* {revenue.revenue_guests if revenue.revenue_guests is not None else '-'}\n"
            f"*{get_translation('revenues.notes')}:* {revenue.revenue_notes if revenue.revenue_notes else '-'}\n\n"
        )

        # --- Summary Section ---
        message += (
            f"*{get_translation('whatsapp.revenue_summary')}*\n"
            f"_{get_translation('revenues.total_additions')}: Rp {total_additions:,.2f}_\n"
            f"_{get_translation('revenues.total_deductions')}: Rp {total_deductions:,.2f}_\n"
            f"*{get_translation('revenues.net_revenue')}: Rp {net_revenue:,.2f}*\n\n"
        )

        # --- Revenue Items Section ---
        if revenue_items:
            message += f"*{get_translation('whatsapp.revenue_items_list')}*\n"
            for item in revenue_items:
                category_symbol = "✅" if item.get_revenue_type_category() == 'Addition' else "❌"
                message += f"- {category_symbol} {item.get_revenue_type_name()}: Rp {item.revenue_item_amount:,.2f}\n"
            message += "\n"

        # --- Compliments Section ---
        if revenue_compliments:
            message += f"*{get_translation('whatsapp.revenue_compliments_list')}*\n"
            for comp in revenue_compliments:
                comp_for = comp.revenue_compliment_for if comp.revenue_compliment_for else '-'
                message += f"- {comp.revenue_compliment_description} ({get_translation('revenues.compliment_for')}: {comp_for})\n"
            message += "\n"

        message += get_translation('whatsapp.thank_you')

        return message
    except Exception as e:
        print(f"Error formatting revenue message: {e}")
        return None
# --- END NEW ---