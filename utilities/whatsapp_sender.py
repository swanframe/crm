# utilities/whatsapp_sender.py
import requests
from models.setting import Setting
from models.store import Store
from models.customer import Customer
from models.reservation import Reservation
from models.revenue import Revenue
from models.store_revenue_target import StoreRevenueTarget
from utilities.localization import get_translation
import calendar
import datetime
from utilities.formatting import format_currency_id, parse_number_id, format_number_id

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
    Includes upcoming reservations for the same store until end of month (max 30).
    """
    try:
        store = Store.find_by_id(reservation.store_id)
        customer = Customer.find_by_id(reservation.customer_id)

        if not store or not customer or not reservation.reservation_datetime:
            return None

        # Format tanggal dan waktu
        date_str = reservation.reservation_datetime.strftime('%d %B %Y')
        time_str = reservation.reservation_datetime.strftime('%H:%M')

        # Pesan utama untuk reservasi yang sedang diinput/diedit
        message = (
            f"{get_translation('whatsapp.greeting')}\n\n"
            f"{get_translation('customers.customer_name')}: {customer.customer_name}\n"
            f"{get_translation('common.telephone')}: {customer.customer_telephone}\n"
            f"{get_translation('stores.store_name')}: {store.store_name}\n"
            f"{get_translation('reservations.reservation_code')}: {reservation.reservation_code}\n"
            f"{get_translation('reservations.reservation_date')}: {date_str}\n"
            f"{get_translation('reservations.reservation_time')}: {time_str}\n"
            f"{get_translation('reservations.reservation_status')}: {get_translation('reservation_statuses.' + reservation.reservation_status)}\n"
        )

        # Add optional fields if they exist
        if reservation.reservation_event:
            message += f"{get_translation('reservations.reservation_event')}: {reservation.reservation_event}\n"
        if reservation.reservation_room:
            message += f"{get_translation('reservations.reservation_room')}: {reservation.reservation_room}\n"
        if reservation.reservation_guests:
            message += f"{get_translation('reservations.reservation_guests')}: {reservation.reservation_guests}\n"
        if reservation.reservation_notes:
            message += f"{get_translation('reservations.reservation_notes')}:\n"
            message += f"{reservation.reservation_notes}\n"

        # --- NEW: Get upcoming reservations for the same store until end of month ---
        # Calculate end of month date
        reservation_date = reservation.reservation_datetime.date()
        last_day = calendar.monthrange(reservation_date.year, reservation_date.month)[1]
        end_of_month = datetime.date(reservation_date.year, reservation_date.month, last_day)
        
        # Get upcoming reservations
        upcoming_reservations = Reservation.get_reservations_by_store_and_date_range(
            store.store_id, 
            reservation_date, 
            end_of_month,
            limit=30
        )
        
        # Remove the current reservation from the list if it's included
        upcoming_reservations = [r for r in upcoming_reservations if r.reservation_id != reservation.reservation_id]
        
        if upcoming_reservations:
            message += f"\n{get_translation('whatsapp.upcoming_reservations')}:\n"
            for i, res in enumerate(upcoming_reservations, 1):
                res_customer = Customer.find_by_id(res.customer_id)
                customer_name = res_customer.customer_name if res_customer else "N/A"
                res_time = res.reservation_datetime.strftime('%d/%m %H:%M') if res.reservation_datetime else "N/A"
                guests = res.reservation_guests or '?'
                message += f"{i}. {res_time} - {customer_name} - {guests} {get_translation('reservations.reservation_guests')}\n"
            
            # Check if there are more than 30 reservations
            if len(upcoming_reservations) >= 30:
                message += f"\n{get_translation('whatsapp.more_reservations_hint')}\n"
        else:
            message += f"\n{get_translation('whatsapp.no_upcoming_reservations')}\n"

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

        # Get current date and target information
        revenue_date = revenue.revenue_date
        target_month = revenue_date.month
        target_year = revenue_date.year
        
        # --- NEW: Enhanced Performance Analysis ---
        # Fetch all targets for the selected year
        revenue_targets_raw = StoreRevenueTarget.find_all_for_store_by_year(revenue.store_id, target_year)
        revenue_targets = {target.target_month: target for target in revenue_targets_raw}
        revenue_target = revenue_targets.get(target_month)
        
        # Calculate accumulated net revenue for the month
        accumulated_net_revenue = Revenue.get_monthly_net_revenue(
            revenue.store_id, 
            target_year, 
            target_month
        )
        
        # Calculate achievement percentage
        achievement_percentage = 0
        if revenue_target and revenue_target.target_amount > 0:
            achievement_percentage = (accumulated_net_revenue / revenue_target.target_amount) * 100

        # --- Message Header ---
        message = (
            f"*📊 {get_translation('whatsapp.revenue_report_title')}*\n\n"
            f"*{get_translation('stores.store_name')}:* {store.store_name}\n"
            f"*{get_translation('revenues.revenue_date')}:* {revenue_date.strftime('%d %B %Y')}\n"
            f"*{get_translation('revenues.guests')}:* {revenue.revenue_guests if revenue.revenue_guests is not None else '-'}\n"
            f"*{get_translation('revenues.notes')}:* {revenue.revenue_notes if revenue.revenue_notes else '-'}\n\n"
        )

        # --- Performance Summary ---
        if revenue_target:
            message += (
                f"*📈 {get_translation('revenues.target_achievement')}*\n"
                f"- {get_translation('revenues.target_amount')}: {format_currency_id(revenue_target.target_amount)}\n"
                f"- {get_translation('revenues.actual_revenue')}: {format_currency_id(accumulated_net_revenue)}\n"
                f"- {get_translation('revenues.monthly_accumulated')}: {achievement_percentage:.2f}%\n\n"
            )

        # --- Revenue Items Section ---
        if revenue_items:
            message += f"*➕➖ {get_translation('whatsapp.revenue_items_list')}*\n"
            for item in revenue_items:
                category_symbol = "➕" if item.get_revenue_type_category() == 'Addition' else "➖"
                message += f"{category_symbol} {item.get_revenue_type_name()}: {format_currency_id(item.revenue_item_amount)}\n"
            message += "\n"

        # --- Summary Section ---
        message += (
            f"*💰 {get_translation('whatsapp.revenue_summary')}*\n"
            f"- {get_translation('revenues.total_additions')}: {format_currency_id(total_additions)}\n"
            f"- {get_translation('revenues.total_deductions')}: {format_currency_id(total_deductions)}\n"
            f"- *{get_translation('revenues.net_revenue')}: {format_currency_id(net_revenue)}*\n\n"
        )

        # --- Compliments Section ---
        if revenue_compliments:
            message += f"*🎁 {get_translation('whatsapp.revenue_compliments_list')}*\n"
            for comp in revenue_compliments:
                comp_for = comp.revenue_compliment_for if comp.revenue_compliment_for else get_translation('common.not_set')
                message += f"- {comp.revenue_compliment_description} ({get_translation('revenues.compliment_for')}: {comp_for})\n"
            message += "\n"

        # --- Performance Notes ---
        if revenue_target:
            # Calculate remaining target and required daily average
            remaining_target = revenue_target.target_amount - accumulated_net_revenue
            days_remaining = (datetime.date(target_year, target_month, calendar.monthrange(target_year, target_month)[1]) - revenue_date).days
            
            if days_remaining > 0:
                required_daily = remaining_target / days_remaining
                message += (
                    f"*📅 {get_translation('whatsapp.performance_notes')}*\n"
                    f"- {get_translation('whatsapp.days_remaining')}: {days_remaining}\n"
                    f"- {get_translation('whatsapp.remaining_target')}: {format_currency_id(net_revenue)}\n"
                    f"- {get_translation('whatsapp.required_daily')}: {format_currency_id(net_revenue)}/hari\n"
                )
            
            if remaining_target > 0 and required_daily > (accumulated_net_revenue / revenue_date.day):
                gap = required_daily - (accumulated_net_revenue / revenue_date.day)
                message += f"- ⚠️ {get_translation('whatsapp.performance_gap_warning').format(gap=format_currency_id(gap))}\n"
            elif remaining_target <= 0:
                message += f"- ✅ {get_translation('whatsapp.target_achieved')}\n"

        message += f"\n{get_translation('whatsapp.thank_you')}"

        return message
    except Exception as e:
        print(f"Error formatting revenue message: {e}")
        return None
# --- END NEW ---