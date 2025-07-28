# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify
from functools import wraps
from config import Config
from models.user import User
from models.store import Store
from models.customer import Customer
from models.store_customer import StoreCustomer
from models.reservation import Reservation # Ensure Reservation is imported
from utilities.security import check_hashed_password, hash_password
from utilities.localization import init_app_localization, get_translation
import math
import datetime
from psycopg2 import errors

app = Flask(__name__)
app.config.from_object(Config)

# Initialize localization for the Flask application
init_app_localization(app)

# Decorator to ensure user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Use translation key for flash message
            flash(get_translation('flash_messages.login_required'), 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# New decorator to check user level
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.user:
                flash(get_translation('flash_messages.login_required'), 'warning')
                return redirect(url_for('login'))
            if g.user.user_level not in allowed_roles:
                flash(get_translation('flash_messages.permission_denied'), 'danger')
                return redirect(url_for('dashboard')) # Redirect to dashboard if no permission
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Populate global 'g' object with the logged-in user
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = None # Default
    if user_id:
        g.user = User.find_by_id(user_id)
        # Ensure g.user has user_level attribute, default if not present
        if g.user and not hasattr(g.user, 'user_level'):
            g.user.user_level = 'Guest' # Default level if not in DB (for compatibility)

@app.route('/')
def index():
    """
    Main route, redirects to dashboard if logged in, or to login page.
    """
    if g.user:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Route for new user registration.
    """
    if g.user: # If already logged in, redirect to dashboard
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not username or not email or not password or not confirm_password:
            flash(get_translation('register.all_fields_required_flash'), 'danger')
        elif password != confirm_password:
            flash(get_translation('register.password_mismatch_flash'), 'danger')
        else:
            # During registration, default level is 'Guest'
            new_user = User.create_new_user(username, email, password, user_level='Guest')
            if new_user:
                flash(get_translation('register.registration_success_flash'), 'success')
                return redirect(url_for('login'))
            else:
                flash(get_translation('register.user_exists_flash'), 'danger')
    return render_template('login.html', register_mode=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Route for user login.
    """
    if g.user: # If already logged in, redirect to dashboard
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']

        user = User.find_one_by(username=username_or_email)
        if not user:
            user = User.find_one_by(email=username_or_email)

        if user and check_hashed_password(user.password_hash, password):
            session['user_id'] = user.id
            flash(get_translation('flash_messages.login_success'), 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(get_translation('login.invalid_credentials_flash'), 'danger')
    return render_template('login.html', register_mode=False)

@app.route('/logout')
@login_required
def logout():
    """
    Route for user logout.
    """
    session.pop('user_id', None)
    flash(get_translation('flash_messages.logout_success'), 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Route for dashboard. Displays summary data.
    """
    total_customers = len(Customer.find_all())
    total_stores = len(Store.find_all())
    total_users = len(User.find_all())
    total_reservations = len(Reservation.find_all())
    
    recent_customers = Customer.find_all()[-5:]
    recent_stores = Store.find_all()[-5:]
    recent_reservations = Reservation.find_all()[-5:]

    users = User.find_all()
    user_map = {user.id: user.username for user in users}

    return render_template('dashboard.html', 
                           total_customers=total_customers,
                           total_stores=total_stores,
                           total_users=total_users,
                           total_reservations=total_reservations,
                           recent_customers=recent_customers,
                           recent_stores=recent_stores,
                           recent_reservations=recent_reservations,
                           user_map=user_map)

@app.route('/profile')
@login_required
def profile():
    """
    Displays the profile page of the logged-in user.
    """
    return render_template('profile.html', user=g.user)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    Displays the settings page and handles password updates.
    """
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']

        user = g.user # Get the logged-in user

        if not check_hashed_password(user.password_hash, old_password):
            flash(get_translation('flash_messages.password_incorrect_old'), 'danger')
        elif not new_password or not confirm_new_password:
            flash(get_translation('flash_messages.password_new_required'), 'danger')
        elif new_password != confirm_new_password:
            flash(get_translation('flash_messages.password_new_mismatch'), 'danger')
        elif len(new_password) < 6: # Example password length validation
            flash(get_translation('flash_messages.password_length_warning'), 'danger')
        else:
            if user.update_password(new_password):
                flash(get_translation('flash_messages.password_update_success'), 'success')
                return redirect(url_for('profile')) # Redirect to profile page after update
            else:
                flash(get_translation('flash_messages.password_update_failed'), 'danger')
    
    return render_template('settings.html')

# --- User Management Routes ---
@app.route('/users')
@login_required
@role_required(['Admin']) # Only Admin can view user list
def list_users():
    """
    Displays a list of all users with search, pagination, and sorting features.
    """
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', type=str)
    sort_by = request.args.get('sort_by', 'id', type=str) # Default sort by 'id'
    sort_order = request.args.get('sort_order', 'asc', type=str) # Default sort order 'asc'
    per_page = 10 # Items per page

    search_columns = ['username', 'email']
    sortable_columns = ['id', 'username', 'email', 'user_level', 'created_at', 'updated_at'] # Sortable columns

    # Validate sort_by to prevent SQL Injection
    if sort_by not in sortable_columns:
        sort_by = 'id' # Fallback to default if column is invalid

    users = User.get_paginated_data(page, per_page, search_query, search_columns, sort_by, sort_order)
    total_users_count = User.count_all(search_query, search_columns)
    
    total_pages = math.ceil(total_users_count / per_page)
    
    return render_template('users.html', 
                           users=users, 
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages,
                           search_query=search_query,
                           sort_by=sort_by, # Pass to template
                           sort_order=sort_order) # Pass to template

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
@role_required(['Admin']) # Only Admin can add users
def add_user():
    """
    Adds a new user.
    """
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        # Get level from form, default 'Guest' if not present or invalid
        user_level = request.form.get('user_level', 'Guest')
        if user_level not in ['Admin', 'Operator', 'Contributor', 'Guest']:
            user_level = 'Guest'

        if not username or not email or not password or not confirm_password:
            flash(get_translation('users.all_fields_required_flash'), 'danger')
        elif password != confirm_password:
            flash(get_translation('users.password_mismatch_flash'), 'danger')
        else:
            new_user = User.create_new_user(username, email, password, user_level) # Pass user_level
            if new_user:
                flash(get_translation('flash_messages.user_added_success_redirect', username=new_user.username), 'success')
                return redirect(url_for('view_user_detail', user_id=new_user.id)) # Redirect to new user's detail
            else:
                flash(get_translation('flash_messages.user_exists_flash'), 'danger')
    return redirect(url_for('list_users'))

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin']) # Only Admin can edit users
def edit_user(user_id):
    """
    Edits an existing user.
    """
    user = User.find_by_id(user_id)
    if not user:
        flash(get_translation('flash_messages.user_not_found'), 'danger')
        return redirect(url_for('list_users'))

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        # Get level from form, default to current user's level if not present or invalid
        new_user_level = request.form.get('user_level', user.user_level)
        if new_user_level not in ['Admin', 'Operator', 'Contributor', 'Guest']:
            new_user_level = user.user_level
        user.user_level = new_user_level

        # Handle password change only if new password fields are provided
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        if new_password and confirm_new_password:
            if new_password != confirm_new_password:
                flash(get_translation('users.password_mismatch_flash'), 'danger')
                return redirect(url_for('view_user_detail', user_id=user.id))
            elif len(new_password) < 6:
                flash(get_translation('flash_messages.password_length_warning'), 'danger')
                return redirect(url_for('view_user_detail', user_id=user.id))
            else:
                user.update_password(new_password) # update_password handles hashing and saving

        if user.save(g.user.id): # Save other changes, passing current user's ID as updated_by
            flash(get_translation('flash_messages.user_updated_success'), 'success')
            return redirect(url_for('view_user_detail', user_id=user.id))
        else:
            flash(get_translation('flash_messages.user_update_failed'), 'danger')
    return redirect(url_for('view_user_detail', user_id=user_id))


@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required(['Admin']) # Only Admin can delete users
def delete_user(user_id):
    """
    Deletes a user.
    """
    user = User.find_by_id(user_id)
    if not user:
        flash(get_translation('flash_messages.user_not_found'), 'danger')
    else:
        if user.id == g.user.id: # Prevent user from deleting their own account
            flash(get_translation('flash_messages.cannot_delete_self'), 'danger')
        else:
            if user.delete():
                flash(get_translation('flash_messages.user_deleted_success'), 'success')
            else:
                flash(get_translation('flash_messages.user_delete_failed'), 'danger')
    return redirect(url_for('list_users'))

@app.route('/users/<int:user_id>')
@login_required
@role_required(['Admin']) # Only Admin can view user details
def view_user_detail(user_id):
    """
    Displays full details of a user.
    """
    user = User.find_by_id(user_id)
    if not user:
        flash(get_translation('flash_messages.user_not_found'), 'danger')
        return redirect(url_for('list_users'))
    
    created_by_user = User.find_by_id(user.created_by) if hasattr(user, 'created_by') and user.created_by else None
    updated_by_user = User.find_by_id(user.updated_by) if hasattr(user, 'updated_by') and user.updated_by else None


    return render_template('user_detail.html', 
                           user=user,
                           created_by_username=created_by_user.username if created_by_user else 'N/A',
                           updated_by_username=updated_by_user.username if updated_by_user else 'N/A')


# --- Store Management Routes ---
@app.route('/stores')
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can view store list
def list_stores():
    """
    Displays a list of all stores with search, pagination, and sorting features.
    """
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', type=str)
    sort_by = request.args.get('sort_by', 'store_id', type=str) # Default sort by 'store_id'
    sort_order = request.args.get('sort_order', 'asc', type=str) # Default sort order 'asc'
    per_page = 10 # Items per page

    # Add new columns to search
    search_columns = ['store_name', 'store_telephone', 'store_email', 'store_address', 'store_whatsapp']
    sortable_columns = ['store_id', 'store_name', 'store_telephone', 'store_email', 'store_address', 'store_whatsapp', 'created_at', 'updated_at'] # Sortable columns

    # Validate sort_by to prevent SQL Injection
    if sort_by not in sortable_columns:
        sort_by = 'store_id' # Fallback to default if column is invalid

    stores = Store.get_paginated_data(page, per_page, search_query, search_columns, sort_by, sort_order)
    total_stores_count = Store.count_all(search_query, search_columns)
    
    total_pages = math.ceil(total_stores_count / per_page)
    
    users = User.find_all()
    user_map = {user.id: user.username for user in users}
    
    return render_template('stores.html', 
                           stores=stores, 
                           user_map=user_map,
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages,
                           search_query=search_query,
                           sort_by=sort_by, # Pass to template
                           sort_order=sort_order) # Pass to template

@app.route('/stores/add', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can add stores
def add_store():
    """
    Adds a new store.
    """
    if request.method == 'POST':
        store_name = request.form['store_name']
        store_telephone = request.form.get('store_telephone') 
        store_email = request.form.get('store_email')         
        store_address = request.form.get('store_address')       
        store_whatsapp = request.form.get('store_whatsapp')     

        if not store_name:
            flash(get_translation('flash_messages.store_name_empty'), 'danger')
        else:
            new_store = Store(
                store_name=store_name, 
                store_telephone=store_telephone, 
                store_email=store_email, 
                store_address=store_address, 
                store_whatsapp=store_whatsapp
            )
            if new_store.save(g.user.id):
                flash(get_translation('flash_messages.store_added_success_redirect', store_name=new_store.store_name), 'success')
                return redirect(url_for('view_store_detail', store_id=new_store.store_id)) # Redirect to new store's detail
            else:
                flash(get_translation('flash_messages.store_add_failed'), 'danger')
    return redirect(url_for('list_stores'))

@app.route('/stores/edit/<int:store_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can edit stores
def edit_store(store_id):
    """
    Edits an existing store.
    """
    store = Store.find_by_id(store_id)
    if not store:
        flash(get_translation('flash_messages.store_not_found'), 'danger')
        return redirect(url_for('list_stores'))

    if request.method == 'POST':
        store.store_name = request.form['store_name']
        store.store_telephone = request.form.get('store_telephone') 
        store.store_email = request.form.get('store_email')         
        store.store_address = request.form.get('store_address')       
        store.store_whatsapp = request.form.get('store_whatsapp')     

        if store.save(g.user.id):
            flash(get_translation('flash_messages.store_updated_success'), 'success')
            return redirect(url_for('view_store_detail', store_id=store.store_id))
        else:
            flash(get_translation('flash_messages.store_update_failed'), 'danger')
    return redirect(url_for('view_store_detail', store_id=store_id))


@app.route('/stores/delete/<int:store_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'Operator']) # Only Admin and Operator can delete stores
def delete_store(store_id):
    """
    Deletes a store.
    """
    store = Store.find_by_id(store_id)
    if not store:
        flash(get_translation('flash_messages.store_not_found'), 'danger')
    else:
        if store.delete():
            flash(get_translation('flash_messages.store_deleted_success'), 'success')
        else:
            flash(get_translation('flash_messages.store_delete_failed'), 'danger')
    return redirect(url_for('list_stores'))

@app.route('/stores/<int:store_id>')
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can view store details
def view_store_detail(store_id):
    """
    Displays full details of a store with paginated associated customers.
    """
    store = Store.find_by_id(store_id)
    if not store:
        flash(get_translation('flash_messages.store_not_found'), 'danger')
        return redirect(url_for('list_stores'))
    
    created_by_user = User.find_by_id(store.created_by)
    updated_by_user = User.find_by_id(store.updated_by)

    # Pagination for associated customers
    page_customers = request.args.get('page_customers', 1, type=int)
    per_page_customers = 5 # Number of associated customers per page
    associated_customers = StoreCustomer.get_paginated_customers_for_store(store_id, page_customers, per_page_customers)
    total_associated_customers_count = StoreCustomer.count_customers_for_store(store_id)
    total_pages_customers = math.ceil(total_associated_customers_count / per_page_customers)

    return render_template('store_detail.html', 
                           store=store, 
                           created_by_username=created_by_user.username if created_by_user else 'N/A',
                           updated_by_username=updated_by_user.username if updated_by_user else 'N/A',
                           associated_customers=associated_customers,
                           page_customers=page_customers,
                           per_page_customers=per_page_customers,
                           total_pages_customers=total_pages_customers)


# --- Customer Management Routes ---
@app.route('/customers')
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can view customer list
def list_customers():
    """
    Displays a list of all customers with search, pagination, and sorting features.
    """
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', type=str)
    sort_by = request.args.get('sort_by', 'customer_id', type=str) # Default sort by 'customer_id'
    sort_order = request.args.get('sort_order', 'asc', type=str) # Default sort order 'asc'
    per_page = 10 # Items per page

    # Add 'customer_code', 'customer_telephone', 'customer_email', 'customer_address', 'customer_whatsapp' to search columns
    search_columns = ['customer_name', 'customer_code', 'customer_is_member', 'customer_organization', 'customer_telephone', 'customer_email', 'customer_address', 'customer_whatsapp'] 
    sortable_columns = ['customer_id', 'customer_name', 'customer_code', 'customer_is_member', 'customer_organization', 'customer_telephone', 'customer_email', 'customer_address', 'customer_whatsapp', 'created_at', 'updated_at'] # Sortable columns

    # Validate sort_by to prevent SQL Injection
    if sort_by not in sortable_columns:
        sort_by = 'customer_id' # Fallback to default if column is invalid

    customers = Customer.get_paginated_data(page, per_page, search_query, search_columns, sort_by, sort_order)
    total_customers_count = Customer.count_all(search_query, search_columns)
    
    total_pages = math.ceil(total_customers_count / per_page)
    
    users = User.find_all()
    user_map = {user.id: user.username for user in users}
    
    return render_template('customers.html', 
                           customers=customers, 
                           user_map=user_map,
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages,
                           search_query=search_query,
                           sort_by=sort_by, # Pass to template
                           sort_order=sort_order) # Pass to template

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can add customers
def add_customer():
    """
    Adds a new customer.
    """
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_code = request.form.get('customer_code')
        customer_is_member = request.form.get('customer_is_member') == 'on'
        customer_organization = request.form.get('customer_organization')
        customer_telephone = request.form.get('customer_telephone') 
        customer_email = request.form.get('customer_email')         
        customer_address = request.form.get('customer_address')       
        customer_whatsapp = request.form.get('customer_whatsapp')     

        if not customer_name:
            flash(get_translation('flash_messages.customer_name_empty'), 'danger')
        else:
            new_customer = Customer(
                customer_name=customer_name, 
                customer_code=customer_code, 
                customer_is_member=customer_is_member,
                customer_organization=customer_organization,
                customer_telephone=customer_telephone, 
                customer_email=customer_email,         
                customer_address=customer_address,     
                customer_whatsapp=customer_whatsapp   
            ) 
            save_success = new_customer.save(g.user.id)
            if save_success:
                flash(get_translation('flash_messages.customer_added_success_redirect', customer_name=new_customer.customer_name), 'success')
                return redirect(url_for('view_customer_detail', customer_id=new_customer.customer_id)) # Redirect to new customer's detail
            else:
                # Check for specific error message from model
                error_message = new_customer.get_last_error()
                if error_message and "duplicate_key_error:customers_customer_code_key" in error_message:
                    flash(get_translation('flash_messages.customer_code_duplicate', code=customer_code), 'danger')
                else:
                    flash(get_translation('flash_messages.customer_add_failed'), 'danger')
    return redirect(url_for('list_customers'))

@app.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can edit customers
def edit_customer(customer_id):
    """
    Edits an existing customer.
    """
    customer = Customer.find_by_id(customer_id)
    if not customer:
        flash(get_translation('flash_messages.customer_not_found'), 'danger')
        return redirect(url_for('list_customers'))

    if request.method == 'POST':
        customer.customer_name = request.form['customer_name']
        customer.customer_code = request.form.get('customer_code')
        customer.customer_is_member = request.form.get('customer_is_member') == 'on'
        customer.customer_organization = request.form.get('customer_organization')
        customer.customer_telephone = request.form.get('customer_telephone') 
        customer.customer_email = request.form.get('customer_email')         
        customer.customer_address = request.form.get('customer_address')       
        customer.customer_whatsapp = request.form.get('customer_whatsapp')     
        
        save_success = customer.save(g.user.id)
        if save_success:
            flash(get_translation('flash_messages.customer_updated_success'), 'success')
            return redirect(url_for('view_customer_detail', customer_id=customer.customer_id))
        else:
            # Check for specific error message from model
            error_message = customer.get_last_error()
            if error_message and "duplicate_key_error:customers_customer_code_key" in error_message:
                flash(get_translation('flash_messages.customer_code_duplicate', code=customer.customer_code), 'danger')
            else:
                flash(get_translation('flash_messages.customer_update_failed'), 'danger')
    return redirect(url_for('view_customer_detail', customer_id=customer_id))

@app.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'Operator']) # Only Admin and Operator can delete customers
def delete_customer(customer_id):
    """
    Deletes a customer.
    """
    customer = Customer.find_by_id(customer_id)
    if not customer:
        flash(get_translation('flash_messages.customer_not_found'), 'danger')
    else:
        if customer.delete():
            flash(get_translation('flash_messages.customer_deleted_success'), 'success')
        else:
            flash(get_translation('flash_messages.customer_delete_failed'), 'danger')
    return redirect(url_for('list_customers'))

@app.route('/customers/<int:customer_id>')
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can view customer details
def view_customer_detail(customer_id):
    """
    Displays full details of a customer with paginated associated stores.
    """
    customer = Customer.find_by_id(customer_id)
    if not customer:
        flash(get_translation('flash_messages.customer_not_found'), 'danger')
        return redirect(url_for('list_customers'))

    created_by_user = User.find_by_id(customer.created_by)
    updated_by_user = User.find_by_id(customer.updated_by)

    # Pagination for associated stores
    page_stores = request.args.get('page_stores', 1, type=int)
    per_page_stores = 5 # Number of associated stores per page
    associated_stores = StoreCustomer.get_paginated_stores_for_customer(customer_id, page_stores, per_page_stores)
    total_associated_stores_count = StoreCustomer.count_stores_for_customer(customer_id)
    total_pages_stores = math.ceil(total_associated_stores_count / per_page_stores)

    return render_template('customer_detail.html', 
                           customer=customer, 
                           created_by_username=created_by_user.username if created_by_user else 'N/A',
                           updated_by_username=updated_by_user.username if updated_by_user else 'N/A',
                           associated_stores=associated_stores,
                           page_stores=page_stores,
                           per_page_stores=per_page_stores,
                           total_pages_stores=total_pages_stores)


# --- Store-Customer Relation Management (Many-to-Many) Routes ---
@app.route('/stores/<int:store_id>/customers', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can manage store-customer associations
def manage_store_customers(store_id):
    """
    Manages customers associated with a specific store.
    Adds pagination and search for the list of available customers.
    """
    store = Store.find_by_id(store_id)
    if not store:
        flash(get_translation('flash_messages.store_not_found'), 'danger')
        return redirect(url_for('list_stores'))

    # Get all customers already associated with this store (without pagination for easier checking)
    # This is needed to know which checkboxes should be checked
    all_associated_customers_raw = StoreCustomer.get_paginated_customers_for_store(store_id, 1, StoreCustomer.count_customers_for_store(store_id) or 1)
    associated_customer_ids = {c.customer_id for c in all_associated_customers_raw}

    # Pagination and search logic for the list of available customers
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', type=str)
    per_page = 10 # Items per page for the association list

    search_columns = ['customer_name', 'customer_code', 'customer_organization'] # Searchable columns

    # Get available customers with pagination and search
    available_customers = Customer.get_paginated_data(page, per_page, search_query, search_columns)
    total_available_customers_count = Customer.count_all(search_query, search_columns)
    total_pages_available_customers = math.ceil(total_available_customers_count / per_page)

    if request.method == 'POST':
        selected_customer_ids = request.form.getlist('customer_ids')
        selected_customer_ids = [int(cid) for cid in selected_customer_ids]

        # Delete associations that are no longer selected
        # Iterate through all existing associations for this store
        for customer in all_associated_customers_raw:
            if customer.customer_id not in selected_customer_ids:
                rel = StoreCustomer(store_id=store_id, customer_id=customer.customer_id)
                rel.delete()
        
        # Add new associations
        for customer_id in selected_customer_ids:
            if customer_id not in associated_customer_ids: # Only add those that don't exist yet
                rel = StoreCustomer(store_id=store_id, customer_id=customer_id)
                rel.save()
        
        flash(get_translation('flash_messages.associations_updated_success', store_name=store.store_name), 'success')
        return redirect(url_for('manage_store_customers', store_id=store_id))

    return render_template('manage_store_customers.html', 
                           store=store, 
                           available_customers=available_customers,
                           associated_customer_ids=associated_customer_ids,
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages_available_customers,
                           search_query=search_query)


@app.route('/customers/<int:customer_id>/stores', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can manage customer-store associations
def manage_customer_stores(customer_id):
    """
    Manages stores associated with a specific customer.
    Adds pagination and search for the list of available stores.
    """
    customer = Customer.find_by_id(customer_id)
    if not customer:
        flash(get_translation('flash_messages.customer_not_found'), 'danger')
        return redirect(url_for('list_customers'))

    # Get all stores already associated with this customer (without pagination for easier checking)
    # This is needed to know which checkboxes should be checked
    all_associated_stores_raw = StoreCustomer.get_paginated_stores_for_customer(customer_id, 1, StoreCustomer.count_stores_for_customer(customer_id) or 1)
    associated_store_ids = {s.store_id for s in all_associated_stores_raw}

    # Pagination and search logic for the list of available stores
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', type=str)
    per_page = 10 # Items per page for the association list

    search_columns = ['store_name', 'store_telephone', 'store_email'] # Searchable columns

    # Get available stores with pagination and search
    available_stores = Store.get_paginated_data(page, per_page, search_query, search_columns)
    total_available_stores_count = Store.count_all(search_query, search_columns)
    total_pages_available_stores = math.ceil(total_available_stores_count / per_page)

    if request.method == 'POST':
        selected_store_ids = request.form.getlist('store_ids')
        selected_store_ids = [int(sid) for sid in selected_store_ids]

        # Delete associations that are no longer selected
        # Iterate through all existing associations for this customer
        for store in all_associated_stores_raw:
            if store.store_id not in selected_store_ids:
                rel = StoreCustomer(store_id=store.store_id, customer_id=customer_id)
                rel.delete()
        
        # Add new associations
        for store_id in selected_store_ids:
            if store_id not in associated_store_ids: # Only add those that don't exist yet
                rel = StoreCustomer(store_id=store_id, customer_id=customer_id)
                rel.save()
        
        flash(get_translation('flash_messages.store_associations_updated_success', customer_name=customer.customer_name), 'success')
        return redirect(url_for('manage_customer_stores', customer_id=customer_id))

    return render_template('manage_customer_stores.html', 
                           customer=customer, 
                           available_stores=available_stores,
                           associated_store_ids=associated_store_ids,
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages_available_stores,
                           search_query=search_query)


# --- Reservation Management Routes ---
@app.route('/reservations')
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can view reservations
def list_reservations():
    """
    Displays a list of all reservations with search, pagination, and sorting features.
    """
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', type=str)
    sort_by = request.args.get('sort_by', 'reservation_id', type=str) # Default sort by 'reservation_id'
    sort_order = request.args.get('sort_order', 'asc', type=str) # Default sort order 'asc'
    per_page = 10 # Items per page

    # Searchable columns for reservations, including customer_name and store_name
    search_columns = ['reservation_status', 'reservation_notes', 'customer_name', 'store_name'] 
    sortable_columns = ['reservation_id', 'customer_name', 'store_name', 'reservation_datetime', 'reservation_status', 'created_at', 'updated_at'] # Added customer_name and store_name to sortable columns
    
    # Validate sort_by to prevent SQL Injection
    if sort_by not in sortable_columns:
        sort_by = 'reservation_id' # Fallback to default if column is invalid

    reservations = Reservation.get_paginated_data(page, per_page, search_query, search_columns, sort_by, sort_order)
    total_reservations_count = Reservation.count_all(search_query, search_columns)
    
    total_pages = math.ceil(total_reservations_count / per_page)
    
    # Fetch all customers and stores for dropdowns in modals (will be replaced by search)
    # For now, keep them as they might be used by other parts or for initial load
    all_customers = Customer.find_all()
    all_stores = Store.find_all()

    return render_template('reservations.html', 
                           reservations=reservations, # FIX: Changed 'reservasi' to 'reservations'
                           all_customers=all_customers, # Keep for now, but will be removed from template usage
                           all_stores=all_stores,
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages,
                           search_query=search_query,
                           sort_by=sort_by,
                           sort_order=sort_order)

@app.route('/reservations/add', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can add reservations
def add_reservation():
    """
    Adds a new reservation.
    """
    if request.method == 'POST':
        customer_id = request.form['customer_id'] 
        store_id = request.form['store_id']
        reservation_datetime_str = request.form['reservation_datetime']
        reservation_status = request.form.get('reservation_status', 'Pending')
        reservation_notes = request.form.get('reservation_notes')
        reservation_event = request.form.get('reservation_event')
        reservation_room = request.form.get('reservation_room')
        reservation_guests = request.form.get('reservation_guests')
        
        # Convert reservation_guests to integer, handle empty string
        if reservation_guests:
            try:
                reservation_guests = int(reservation_guests)
            except ValueError:
                flash(get_translation('flash_messages.reservation_guests_invalid'), 'danger')
                return redirect(url_for('list_reservations'))
        else:
            reservation_guests = None # Store as None if empty

        if not customer_id or not store_id or not reservation_datetime_str:
            flash(get_translation('flash_messages.reservation_all_fields_required'), 'danger')
        else:
            try:
                # Convert datetime-local string to datetime object
                reservation_datetime = datetime.datetime.fromisoformat(reservation_datetime_str)
                
                new_reservation = Reservation(
                    customer_id=int(customer_id),
                    store_id=int(store_id),
                    reservation_datetime=reservation_datetime,
                    reservation_status=reservation_status,
                    reservation_notes=reservation_notes,
                    reservation_event=reservation_event,
                    reservation_room=reservation_room,
                    reservation_guests=reservation_guests
                    # reservation_code will be generated in the save method if not provided
                )
                if new_reservation.save(g.user.id):
                    flash(get_translation('flash_messages.reservation_added_success_redirect', reservation_id=new_reservation.reservation_id), 'success')
                    return redirect(url_for('view_reservation_detail', reservation_id=new_reservation.reservation_id))
                else:
                    flash(get_translation('flash_messages.reservation_add_failed'), 'danger')
            except ValueError:
                flash(get_translation('flash_messages.reservation_date_invalid'), 'danger')
            except Exception as e:
                flash(get_translation('flash_messages.reservation_add_failed_generic', error=str(e)), 'danger')
    return redirect(url_for('list_reservations'))

@app.route('/reservations/edit/<int:reservation_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can edit reservations
def edit_reservation(reservation_id):
    """
    Edits an existing reservation.
    """
    reservation = Reservation.find_by_id(reservation_id)
    if not reservation:
        flash(get_translation('flash_messages.reservation_not_found'), 'danger')
        return redirect(url_for('list_reservations'))

    if request.method == 'POST':
        reservation.customer_id = int(request.form['customer_id']) 
        reservation.store_id = int(request.form['store_id'])
        reservation_datetime_str = request.form['reservation_datetime']
        reservation.reservation_status = request.form.get('reservation_status', 'Pending')
        reservation.reservation_notes = request.form.get('reservation_notes')
        reservation.reservation_event = request.form.get('reservation_event')
        reservation.reservation_room = request.form.get('reservation_room')
        reservation_guests = request.form.get('reservation_guests')

        # Convert reservation_guests to integer, handle empty string
        if reservation_guests:
            try:
                reservation.reservation_guests = int(reservation_guests)
            except ValueError:
                flash(get_translation('flash_messages.reservation_guests_invalid'), 'danger')
                return redirect(url_for('view_reservation_detail', reservation_id=reservation.reservation_id))
        else:
            reservation.reservation_guests = None # Store as None if empty

        try:
            reservation.reservation_datetime = datetime.datetime.fromisoformat(reservation_datetime_str)
            if reservation.save(g.user.id):
                flash(get_translation('flash_messages.reservation_updated_success'), 'success')
                return redirect(url_for('view_reservation_detail', reservation_id=reservation.reservation_id))
            else:
                flash(get_translation('flash_messages.reservation_update_failed'), 'danger')
        except ValueError:
            flash(get_translation('flash_messages.reservation_date_invalid'), 'danger')
        except Exception as e:
            flash(get_translation('flash_messages.reservation_update_failed_generic', error=str(e)), 'danger')
    return redirect(url_for('view_reservation_detail', reservation_id=reservation_id))

@app.route('/reservations/delete/<int:reservation_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'Operator']) # Only Admin and Operator can delete reservations
def delete_reservation(reservation_id):
    """
    Deletes a reservation.
    """
    reservation = Reservation.find_by_id(reservation_id)
    if not reservation:
        flash(get_translation('flash_messages.reservation_not_found'), 'danger')
    else:
        if reservation.delete():
            flash(get_translation('flash_messages.reservation_deleted_success'), 'success')
        else:
            flash(get_translation('flash_messages.reservation_delete_failed'), 'danger')
    return redirect(url_for('list_reservations'))

@app.route('/reservations/<int:reservation_id>')
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor can view reservation details
def view_reservation_detail(reservation_id):
    """
    Displays full details of a reservation.
    """
    reservation = Reservation.find_by_id(reservation_id)
    if not reservation:
        flash(get_translation('flash_messages.reservation_not_found'), 'danger')
        return redirect(url_for('list_reservations'))
    
    created_by_user = User.find_by_id(reservation.created_by) if hasattr(reservation, 'created_by') and reservation.created_by else None
    updated_by_user = User.find_by_id(reservation.updated_by) if hasattr(reservation, 'updated_by') and reservation.updated_by else None

    # Fetch the full customer details
    customer_details = reservation.get_customer_details()

    # Fetch all customers and stores for dropdowns in modals (will be replaced by search)
    # For now, keep them as they might be used by other parts or for initial load
    all_customers = Customer.find_all()
    all_stores = Store.find_all()

    return render_template('reservation_detail.html', 
                           reservation=reservation,
                           customer_details=customer_details, # Pass customer_details to the template
                           created_by_username=created_by_user.username if created_by_user else 'N/A',
                           updated_by_username=updated_by_user.username if updated_by_user else 'N/A',
                           all_customers=all_customers, # Keep for now, but will be removed from template usage
                           all_stores=all_stores)

# NEW: API endpoint for customer search
@app.route('/api/customers/search')
@login_required
def search_customers():
    """
    API endpoint to search for customers by name or code.
    Returns a JSON list of matching customers (id, name, code).
    """
    query = request.args.get('q', '')
    # Limit results for performance
    # Search by customer_name and customer_code
    customers = Customer.get_paginated_data(
        page=1, 
        per_page=10, # Limit to 10 results for autocomplete
        search_query=query, 
        search_columns=['customer_name', 'customer_code']
    )
    
    results = []
    for customer in customers:
        results.append({
            'id': customer.customer_id,
            'name': customer.customer_name,
            'code': customer.customer_code if customer.customer_code else ''
        })
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)