from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from functools import wraps
from config import Config
from models.user import User
from models.store import Store
from models.customer import Customer
from models.store_customer import StoreCustomer
from utilities.security import check_hashed_password, hash_password
from utilities.localization import init_app_localization, get_translation
import math
from psycopg2 import errors # Import modul errors dari psycopg2

app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi lokalisasi untuk aplikasi Flask
init_app_localization(app)

# Decorator untuk memastikan user sudah login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Menggunakan kunci terjemahan untuk pesan flash
            flash(get_translation('flash_messages.login_required'), 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator baru untuk memeriksa level pengguna
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.user:
                flash(get_translation('flash_messages.login_required'), 'warning')
                return redirect(url_for('login'))
            if g.user.user_level not in allowed_roles:
                flash(get_translation('flash_messages.permission_denied'), 'danger')
                return redirect(url_for('dashboard')) # Arahkan ke dashboard jika tidak ada izin
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Mengisi objek global 'g' dengan user yang sedang login
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = None # Default
    if user_id:
        g.user = User.find_by_id(user_id)
        # Pastikan g.user memiliki atribut user_level, default jika tidak ada
        if g.user and not hasattr(g.user, 'user_level'):
            g.user.user_level = 'Guest' # Default level jika tidak ada di DB (untuk kompatibilitas)

@app.route('/')
def index():
    """
    Rute utama, mengarahkan ke dashboard jika login, atau ke halaman login.
    """
    if g.user:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Rute untuk registrasi user baru.
    """
    if g.user: # Jika sudah login, arahkan ke dashboard
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
            # Saat registrasi, level default adalah 'Guest'
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
    Rute untuk login user.
    """
    if g.user: # Jika sudah login, arahkan ke dashboard
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
    Rute untuk logout user.
    """
    session.pop('user_id', None)
    flash(get_translation('flash_messages.logout_success'), 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Rute untuk dashboard. Menampilkan data ringkasan.
    """
    total_customers = len(Customer.find_all())
    total_stores = len(Store.find_all())
    total_users = len(User.find_all()) # Tambahkan total users
    
    recent_customers = Customer.find_all()[-5:]
    recent_stores = Store.find_all()[-5:]

    users = User.find_all()
    user_map = {user.id: user.username for user in users}

    return render_template('dashboard.html', 
                           total_customers=total_customers,
                           total_stores=total_stores,
                           total_users=total_users, # Teruskan ke template
                           recent_customers=recent_customers,
                           recent_stores=recent_stores,
                           user_map=user_map)

@app.route('/profile')
@login_required
def profile():
    """
    Menampilkan halaman profil pengguna yang sedang login.
    """
    return render_template('profile.html', user=g.user)

@app.route('/settings', methods=['GET', 'POST']) # Rute baru untuk halaman settings
@login_required
def settings():
    """
    Menampilkan halaman pengaturan dan menangani pembaruan password.
    """
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']

        user = g.user # Ambil user yang sedang login

        if not check_hashed_password(user.password_hash, old_password):
            flash(get_translation('flash_messages.password_incorrect_old'), 'danger')
        elif not new_password or not confirm_new_password:
            flash(get_translation('flash_messages.password_new_required'), 'danger')
        elif new_password != confirm_new_password:
            flash(get_translation('flash_messages.password_new_mismatch'), 'danger')
        elif len(new_password) < 6: # Contoh validasi panjang password
            flash(get_translation('flash_messages.password_length_warning'), 'danger')
        else:
            if user.update_password(new_password):
                flash(get_translation('flash_messages.password_update_success'), 'success')
                return redirect(url_for('profile')) # Redirect ke halaman profil setelah update
            else:
                flash(get_translation('flash_messages.password_update_failed'), 'danger')
    
    return render_template('settings.html')

# --- Rute Manajemen Users ---
@app.route('/users')
@login_required
@role_required(['Admin']) # Hanya Admin yang bisa melihat daftar user
def list_users():
    """
    Menampilkan daftar semua user dengan fitur pencarian, pagination, dan penyortiran.
    """
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', type=str)
    sort_by = request.args.get('sort_by', 'id', type=str) # Default sort by 'id'
    sort_order = request.args.get('sort_order', 'asc', type=str) # Default sort order 'asc'
    per_page = 10 # Jumlah item per halaman

    search_columns = ['username', 'email']
    sortable_columns = ['id', 'username', 'email', 'user_level', 'created_at', 'updated_at'] # Kolom yang bisa disortir

    # Validasi sort_by untuk mencegah SQL Injection
    if sort_by not in sortable_columns:
        sort_by = 'id' # Fallback ke default jika kolom tidak valid

    users = User.get_paginated_data(page, per_page, search_query, search_columns, sort_by, sort_order)
    total_users_count = User.count_all(search_query, search_columns)
    
    total_pages = math.ceil(total_users_count / per_page)
    
    return render_template('users.html', 
                           users=users, 
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages,
                           search_query=search_query,
                           sort_by=sort_by, # Teruskan ke template
                           sort_order=sort_order) # Teruskan ke template

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
@role_required(['Admin']) # Hanya Admin yang bisa menambah user
def add_user():
    """
    Menambahkan user baru.
    """
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        # Mengambil level dari form, default 'Guest' jika tidak ada atau tidak valid
        user_level = request.form.get('user_level', 'Guest')
        if user_level not in ['Admin', 'Operator', 'Contributor', 'Guest']:
            user_level = 'Guest'

        if not username or not email or not password or not confirm_password:
            flash(get_translation('users.all_fields_required_flash'), 'danger')
        elif password != confirm_password:
            flash(get_translation('users.password_mismatch_flash'), 'danger')
        else:
            new_user = User.create_new_user(username, email, password, user_level) # Meneruskan user_level
            if new_user:
                flash(get_translation('flash_messages.user_added_success_redirect', username=new_user.username), 'success')
                return redirect(url_for('view_user_detail', user_id=new_user.id)) # Redirect ke detail user baru
            else:
                flash(get_translation('flash_messages.user_exists_flash'), 'danger')
    return redirect(url_for('list_users'))

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin']) # Hanya Admin yang bisa mengedit user
def edit_user(user_id):
    """
    Mengedit user yang sudah ada.
    """
    user = User.find_by_id(user_id)
    if not user:
        flash(get_translation('flash_messages.user_not_found'), 'danger')
        return redirect(url_for('list_users'))

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        # Mengambil level dari form, default ke level user saat ini jika tidak ada atau tidak valid
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
@role_required(['Admin']) # Hanya Admin yang bisa menghapus user
def delete_user(user_id):
    """
    Menghapus user.
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
@role_required(['Admin']) # Hanya Admin yang bisa melihat detail user
def view_user_detail(user_id):
    """
    Menampilkan detail lengkap satu user.
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


# --- Rute Manajemen Stores ---
@app.route('/stores')
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor bisa melihat daftar toko
def list_stores():
    """
    Menampilkan daftar semua toko dengan fitur pencarian, pagination, dan penyortiran.
    """
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', type=str)
    sort_by = request.args.get('sort_by', 'store_id', type=str) # Default sort by 'store_id'
    sort_order = request.args.get('sort_order', 'asc', type=str) # Default sort order 'asc'
    per_page = 10 # Jumlah item per halaman

    # Tambahkan kolom baru ke pencarian
    search_columns = ['store_name', 'store_telephone', 'store_email', 'store_address', 'store_whatsapp']
    sortable_columns = ['store_id', 'store_name', 'store_telephone', 'store_email', 'store_address', 'store_whatsapp', 'created_at', 'updated_at'] # Kolom yang bisa disortir

    # Validasi sort_by untuk mencegah SQL Injection
    if sort_by not in sortable_columns:
        sort_by = 'store_id' # Fallback ke default jika kolom tidak valid

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
                           sort_by=sort_by, # Teruskan ke template
                           sort_order=sort_order) # Teruskan ke template

@app.route('/stores/add', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor bisa menambah toko
def add_store():
    """
    Menambahkan toko baru.
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
                return redirect(url_for('view_store_detail', store_id=new_store.store_id)) # Redirect ke detail store baru
            else:
                flash(get_translation('flash_messages.store_add_failed'), 'danger')
    return redirect(url_for('list_stores'))

@app.route('/stores/edit/<int:store_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor bisa mengedit toko
def edit_store(store_id):
    """
    Mengedit toko yang sudah ada.
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
@role_required(['Admin', 'Operator']) # Hanya Admin dan Operator yang bisa menghapus toko
def delete_store(store_id):
    """
    Menghapus toko.
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
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor bisa melihat detail toko
def view_store_detail(store_id):
    """
    Menampilkan detail lengkap satu toko dengan pelanggan terkait yang dipaginasi.
    """
    store = Store.find_by_id(store_id)
    if not store:
        flash(get_translation('flash_messages.store_not_found'), 'danger')
        return redirect(url_for('list_stores'))
    
    created_by_user = User.find_by_id(store.created_by)
    updated_by_user = User.find_by_id(store.updated_by)

    # Pagination untuk associated customers
    page_customers = request.args.get('page_customers', 1, type=int)
    per_page_customers = 5 # Jumlah pelanggan terkait per halaman
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


# --- Rute Manajemen Customers ---
@app.route('/customers')
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor bisa melihat daftar pelanggan
def list_customers():
    """
    Menampilkan daftar semua pelanggan dengan fitur pencarian, pagination, dan penyortiran.
    """
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', type=str)
    sort_by = request.args.get('sort_by', 'customer_id', type=str) # Default sort by 'customer_id'
    sort_order = request.args.get('sort_order', 'asc', type=str) # Default sort order 'asc'
    per_page = 10 # Jumlah item per halaman

    # Tambahkan 'customer_code', 'customer_telephone', 'customer_email', 'customer_address', 'customer_whatsapp' ke kolom pencarian
    search_columns = ['customer_name', 'customer_code', 'customer_is_member', 'customer_organization', 'customer_telephone', 'customer_email', 'customer_address', 'customer_whatsapp'] 
    sortable_columns = ['customer_id', 'customer_name', 'customer_code', 'customer_is_member', 'customer_organization', 'customer_telephone', 'customer_email', 'customer_address', 'customer_whatsapp', 'created_at', 'updated_at'] # Kolom yang bisa disortir

    # Validasi sort_by untuk mencegah SQL Injection
    if sort_by not in sortable_columns:
        sort_by = 'customer_id' # Fallback ke default jika kolom tidak valid

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
                           sort_by=sort_by, # Teruskan ke template
                           sort_order=sort_order) # Teruskan ke template

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor bisa menambah pelanggan
def add_customer():
    """
    Menambahkan pelanggan baru.
    """
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_code = request.form.get('customer_code')
        customer_is_member = request.form.get('customer_is_member') == 'on' # <-- Ubah nama atribut
        customer_organization = request.form.get('customer_organization')   # <-- Ubah nama atribut
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
                customer_is_member=customer_is_member, # <-- Inisialisasi atribut baru
                customer_organization=customer_organization, # <-- Inisialisasi atribut baru
                customer_telephone=customer_telephone, 
                customer_email=customer_email,         
                customer_address=customer_address,     
                customer_whatsapp=customer_whatsapp   
            ) 
            save_success = new_customer.save(g.user.id)
            if save_success:
                flash(get_translation('flash_messages.customer_added_success_redirect', customer_name=new_customer.customer_name), 'success')
                return redirect(url_for('view_customer_detail', customer_id=new_customer.customer_id)) # Redirect ke detail customer baru
            else:
                # Periksa pesan error spesifik dari model
                error_message = new_customer.get_last_error()
                if error_message and "duplicate_key_error:customers_customer_code_key" in error_message:
                    flash(get_translation('flash_messages.customer_code_duplicate', code=customer_code), 'danger')
                else:
                    flash(get_translation('flash_messages.customer_add_failed'), 'danger')
    return redirect(url_for('list_customers'))

@app.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor bisa mengedit pelanggan
def edit_customer(customer_id):
    """
    Mengedit pelanggan yang sudah ada.
    """
    customer = Customer.find_by_id(customer_id)
    if not customer:
        flash(get_translation('flash_messages.customer_not_found'), 'danger')
        return redirect(url_for('list_customers'))

    if request.method == 'POST':
        customer.customer_name = request.form['customer_name']
        customer.customer_code = request.form.get('customer_code')
        customer.customer_is_member = request.form.get('customer_is_member') == 'on' # <-- Ubah nama atribut
        customer.customer_organization = request.form.get('customer_organization')   # <-- Ubah nama atribut
        customer.customer_telephone = request.form.get('customer_telephone') 
        customer.customer_email = request.form.get('customer_email')         
        customer.customer_address = request.form.get('customer_address')       
        customer.customer_whatsapp = request.form.get('customer_whatsapp')     
        
        save_success = customer.save(g.user.id)
        if save_success:
            flash(get_translation('flash_messages.customer_updated_success'), 'success')
            return redirect(url_for('view_customer_detail', customer_id=customer.customer_id))
        else:
            # Periksa pesan error spesifik dari model
            error_message = customer.get_last_error()
            if error_message and "duplicate_key_error:customers_customer_code_key" in error_message:
                flash(get_translation('flash_messages.customer_code_duplicate', code=customer.customer_code), 'danger')
            else:
                flash(get_translation('flash_messages.customer_update_failed'), 'danger')
    return redirect(url_for('view_customer_detail', customer_id=customer_id))

@app.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
@role_required(['Admin', 'Operator']) # Hanya Admin dan Operator yang bisa menghapus pelanggan
def delete_customer(customer_id):
    """
    Menghapus pelanggan.
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
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor bisa melihat detail pelanggan
def view_customer_detail(customer_id):
    """
    Menampilkan detail lengkap satu pelanggan dengan toko terkait yang dipaginasi.
    """
    customer = Customer.find_by_id(customer_id)
    if not customer:
        flash(get_translation('flash_messages.customer_not_found'), 'danger')
        return redirect(url_for('list_customers'))

    created_by_user = User.find_by_id(customer.created_by)
    updated_by_user = User.find_by_id(customer.updated_by)

    # Pagination untuk associated stores
    page_stores = request.args.get('page_stores', 1, type=int)
    per_page_stores = 5 # Jumlah toko terkait per halaman
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


# --- Rute Manajemen Relasi Store-Customer (Many-to-Many) ---
@app.route('/stores/<int:store_id>/customers', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor bisa mengelola asosiasi toko-pelanggan
def manage_store_customers(store_id):
    """
    Mengelola pelanggan yang terkait dengan toko tertentu.
    Menambahkan paginasi dan pencarian untuk daftar pelanggan yang tersedia.
    """
    store = Store.find_by_id(store_id)
    if not store:
        flash(get_translation('flash_messages.store_not_found'), 'danger')
        return redirect(url_for('list_stores'))

    # Ambil semua pelanggan yang sudah terkait dengan toko ini (tanpa paginasi untuk mempermudah pengecekan)
    # Ini diperlukan untuk mengetahui checkbox mana yang harus dicentang
    all_associated_customers_raw = StoreCustomer.get_paginated_customers_for_store(store_id, 1, StoreCustomer.count_customers_for_store(store_id) or 1)
    associated_customer_ids = {c.customer_id for c in all_associated_customers_raw}

    # Logika paginasi dan pencarian untuk daftar pelanggan yang tersedia
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', type=str)
    per_page = 10 # Jumlah item per halaman untuk daftar asosiasi

    search_columns = ['customer_name', 'customer_code', 'customer_organization'] # Kolom yang bisa dicari

    # Ambil pelanggan yang tersedia dengan paginasi dan pencarian
    available_customers = Customer.get_paginated_data(page, per_page, search_query, search_columns)
    total_available_customers_count = Customer.count_all(search_query, search_columns)
    total_pages_available_customers = math.ceil(total_available_customers_count / per_page)

    if request.method == 'POST':
        selected_customer_ids = request.form.getlist('customer_ids')
        selected_customer_ids = [int(cid) for cid in selected_customer_ids]

        # Hapus asosiasi yang tidak lagi dipilih
        # Iterasi melalui semua asosiasi yang ada untuk toko ini
        for customer in all_associated_customers_raw:
            if customer.customer_id not in selected_customer_ids:
                rel = StoreCustomer(store_id=store_id, customer_id=customer.customer_id)
                rel.delete()
        
        # Tambahkan asosiasi baru
        for customer_id in selected_customer_ids:
            if customer_id not in associated_customer_ids: # Hanya tambahkan yang belum ada
                rel = StoreCustomer(store_id=store_id, customer_id=customer_id)
                rel.save()
        
        flash(get_translation('flash_messages.associations_updated_success', store_name=store.store_name), 'success')
        return redirect(url_for('manage_store_customers', store_id=store_id))

    return render_template('manage_store_customers.html', 
                           store=store, 
                           available_customers=available_customers, # Mengganti all_customers
                           associated_customer_ids=associated_customer_ids,
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages_available_customers,
                           search_query=search_query)


@app.route('/customers/<int:customer_id>/stores', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Operator', 'Contributor']) # Admin, Operator, Contributor bisa mengelola asosiasi pelanggan-toko
def manage_customer_stores(customer_id):
    """
    Mengelola toko yang terkait dengan pelanggan tertentu.
    Menambahkan paginasi dan pencarian untuk daftar toko yang tersedia.
    """
    customer = Customer.find_by_id(customer_id)
    if not customer:
        flash(get_translation('flash_messages.customer_not_found'), 'danger')
        return redirect(url_for('list_customers'))

    # Ambil semua toko yang sudah terkait dengan pelanggan ini (tanpa paginasi untuk mempermudah pengecekan)
    # Ini diperlukan untuk mengetahui checkbox mana yang harus dicentang
    all_associated_stores_raw = StoreCustomer.get_paginated_stores_for_customer(customer_id, 1, StoreCustomer.count_stores_for_customer(customer_id) or 1)
    associated_store_ids = {s.store_id for s in all_associated_stores_raw}

    # Logika paginasi dan pencarian untuk daftar toko yang tersedia
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', type=str)
    per_page = 10 # Jumlah item per halaman untuk daftar asosiasi

    search_columns = ['store_name', 'store_telephone', 'store_email'] # Kolom yang bisa dicari

    # Ambil toko yang tersedia dengan paginasi dan pencarian
    available_stores = Store.get_paginated_data(page, per_page, search_query, search_columns)
    total_available_stores_count = Store.count_all(search_query, search_columns)
    total_pages_available_stores = math.ceil(total_available_stores_count / per_page)

    if request.method == 'POST':
        selected_store_ids = request.form.getlist('store_ids')
        selected_store_ids = [int(sid) for sid in selected_store_ids]

        # Hapus asosiasi yang tidak lagi dipilih
        # Iterasi melalui semua asosiasi yang ada untuk pelanggan ini
        for store in all_associated_stores_raw:
            if store.store_id not in selected_store_ids:
                rel = StoreCustomer(store_id=store.store_id, customer_id=customer_id)
                rel.delete()
        
        # Tambahkan asosiasi baru
        for store_id in selected_store_ids:
            if store_id not in associated_store_ids: # Hanya tambahkan yang belum ada
                rel = StoreCustomer(store_id=store_id, customer_id=customer_id)
                rel.save()
        
        flash(get_translation('flash_messages.store_associations_updated_success', customer_name=customer.customer_name), 'success')
        return redirect(url_for('manage_customer_stores', customer_id=customer_id))

    return render_template('manage_customer_stores.html', 
                           customer=customer, 
                           available_stores=available_stores, # Mengganti all_stores
                           associated_store_ids=associated_store_ids,
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages_available_stores,
                           search_query=search_query)


if __name__ == '__main__':
    app.run(debug=True)