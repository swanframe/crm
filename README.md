# CRM System

A simple Customer Relationship Management (CRM) system built with Flask and PostgreSQL. This project allows users to manage customers, stores, user accounts, reservations, and includes revenue management with monthly revenue targets for each store. It features role-based access control, multi-language support, and a many-to-many relationship between stores and customers.

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [License](#license)
- [Contact](#contact)

## Features

- **User Authentication and Registration**: Secure login and signup with password hashing.
- **Role-Based Access Control**: Supports roles like Admin, Operator, Contributor, and Guest with different permissions.
- **Customer Management**: Add, edit, delete customers with pagination, search, and sorting capabilities.
- **Store Management**: Add, edit, delete stores with pagination, search, and sorting capabilities.
- **Reservation Management**: Add, edit, delete reservations with pagination, search, and sorting capabilities. Includes customer and store associations.
- **Revenue Management**: Add, edit, delete revenue entries with pagination, search, and sorting capabilities. Includes revenue types, items, and compliments.
- **Store Revenue Targets**: Set, view, edit, and delete monthly revenue targets for each store, accessible via store details.
- **Revenue Analytics**: Interactive chart with date range selection, multi-store selection, group by day/week/month, chart type line/bar/stacked, optional cumulative view, and monthly target overlay.
- **Many-to-Many Relationship**: Manage associations between stores and customers.
- **User Profile and Settings**: View profile and update password.
- **Multi-Language Support**: Available in English, Indonesian, and Chinese.
- **Localized Number Formatting**: Supports Indonesian/European number and currency formats (e.g., 1.000,00 instead of 1,000.00).
- **Secure Password Hashing**: Uses Werkzeug for password security.
- **Enhanced WhatsApp Notification Integration**: When adding or editing a reservation, the WhatsApp message includes not only the current reservation details but also a list of upcoming reservations (up to 30) for the same store until the end of the month. If the store's WhatsApp number is not set, the message cannot be sent. The API token (for services like Fonnte) is securely stored in the database and can only be edited by Admin users via a dedicated settings page. This feature is optional and non-essential; the application functions fully without it.
- **Public Reservation**: Customers can make reservations directly via embeddable forms on store websites (no login required). Includes public detail page for viewing reservation status by code and phone number. Supports optional WhatsApp notifications to store.

## Project Structure

Below is the structure of the project directory:

```
crm/
├── app.py                  # Main application entry point (updated with public reservation routes)
├── config.py               # Configuration settings
├── requirements.txt        # Dependencies
├── .env                    # Environment variables (not tracked in Git)
├── models/
│   ├── __init__.py         # Package initialization
│   ├── base_model.py       # Base model with common CRUD functionality
│   ├── user.py             # User model
│   ├── store.py            # Store model
│   ├── customer.py         # Customer model
│   ├── store_customer.py   # Many-to-many relation model for stores and customers
│   ├── reservation.py      # Reservation model
│   ├── revenue.py          # Revenue model
│   ├── revenue_type.py     # Revenue Type model
│   ├── revenue_item.py     # Revenue Item model
│   ├── revenue_compliment.py # Revenue Compliment model
│   ├── store_revenue_target.py # Store Revenue Target model
│   └── setting.py          # Settings model (for storing key-value pairs like WhatsApp API token)
├── templates/
│   ├── base.html           # Base template for all pages
│   ├── login.html          # Login and registration page
│   ├── dashboard.html      # Main dashboard page
│   ├── stores.html         # Store management page
│   ├── customers.html      # Customer management page
│   ├── manage_store_customers.html # Manage customers for a store
│   ├── manage_customer_stores.html # Manage stores for a customer
│   ├── store_detail.html   # Store detail page
│   ├── customer_detail.html # Customer detail page
│   ├── profile.html        # User profile page
│   ├── settings.html       # User settings page
│   ├── users.html          # User management page
│   ├── user_detail.html    # User detail page
│   ├── reservations.html   # Reservation management page
│   ├── reservation_detail.html # Reservation detail page
│   ├── revenue_types.html  # Revenue Type management page
│   ├── revenues.html       # Revenue management page
│   ├── revenue_detail.html # Revenue detail page
│   ├── whatsapp_settings.html # WhatsApp settings page (Admin-only)
│   ├── public_reservation_detail.html # Public reservation detail page (no login required)
│   ├── public_reservation_not_found.html # Public not-found page for invalid reservation queries
│   └── analytics_revenue.html # Revenue Analytics page (filters + chart + summary)
├── utilities/
│   ├── security.py         # Password hashing utilities
│   ├── localization.py     # Multi-language translation utilities
│   ├── formatting.py       # Number and currency formatting utilities
│   └── whatsapp_sender.py  # WhatsApp message sending utilities (enhanced to include upcoming reservations)
├── static/
│   └── snippets/           # Example HTML snippets for embedding on external store websites
│       ├── reservation-form-only.html # Embeddable form for public reservations
│       └── check-status-form-only.html # Embeddable form for checking reservation status
└── translations/
    ├── en.json             # English translations
    ├── id.json             # Indonesian translations
    └── zh.json             # Chinese translations
```

**Notes:**

* Chart rendering uses **Chart.js** via CDN.

## Installation

To set up the project locally, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/swanframe/crm.git
   cd crm
   ```

2. **Create a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   - Create a `.env` file in the root directory with the following content:
     ```env
     SECRET_KEY=your_very_secret_key_here
     DATABASE_URL=postgresql://postgres:your_password@localhost:5432/crm_db
     FLASK_DEBUG=1
     ```

## Usage

- **Login**: Navigate to `/login` to access the login page.
- **Register**: New users can sign up at `/register` (default role: Guest).
- **Dashboard**: After login, users are redirected to `/dashboard` for an overview.
- **Manage Customers**: Go to `/customers` to perform CRUD operations on customers (requires Admin, Operator, or Contributor role).
- **Manage Stores**: Go to `/stores` to perform CRUD operations on stores (requires Admin, Operator, or Contributor role).
- **Manage Reservations**: Go to `/reservations` to perform CRUD operations on reservations (requires Admin, Operator, or Contributor role). When adding or editing a reservation, an optional checkbox allows sending details to the store's WhatsApp number (if configured). The WhatsApp message now includes a list of upcoming reservations for the same store until the end of the month (limited to 30 reservations).
- **Manage Revenues**: Go to `/revenues` to perform CRUD operations on revenue entries (requires Admin, Operator, or Contributor role). From the revenue detail page (`/revenues/<revenue_id>`), users can send a revenue report to the store's WhatsApp number (if configured).
- **Manage Revenue Types**: Go to `/revenue_types` to perform CRUD operations on revenue types (requires Admin or Operator role).
- **Manage Revenue Targets**: View, add, edit, and delete monthly revenue targets for a store in the store detail page (`/stores/<store_id>`).
- **Manage Users**: Admins can manage users at `/users`.
- **Profile and Settings**: Access `/profile` and `/settings` for user account management.
- **WhatsApp Settings** (Optional): Admins can configure the WhatsApp API token (e.g., for Fonnte) at `/whatsapp_settings`. This enables the enhanced WhatsApp notification feature for reservations (including upcoming reservations list) and revenue reports. If not configured, the sending options will be disabled or ineffective.
- **Public Reservation Integration**: Customers can make reservations without logging in via embeddable HTML forms on store websites. Copy the snippets from `static/snippets/` and paste into your store's website (e.g., homepage). 
  - **reservation-form-only.html**: Form for submitting reservations. Customize `store_id`, `whatsapp_target`, and `CRM_ENDPOINT` in the script to match your CRM domain (e.g., `https://crm.example.com`).
  - **check-status-form-only.html**: Form for checking reservation status by code and phone. Customize `FALLBACK_CRM_BASE` to your CRM domain.
  - After submission, users are redirected to a public detail page (e.g., `/public/reservations/<code>/<phone>`). Supports CORS for cross-origin requests from store sites.
* **Revenue Analytics**: Navigate via sidebar Revenues → Revenue Analytics or open `/analytics/revenue`. Choose date range, stores, grouping (day/week/month), chart type (line/bar/stacked), toggle cumulative and monthly target overlay.

## Screenshots

### Dashboard
![Dashboard App](images/dashboard.png)
*CRM application main dashboard view*

### Customer Management
![Customer Management](images/customer-management.png)
*Customer data management with search feature*

## Configuration

Configuration is managed through `config.py` and environment variables:

- **SECRET_KEY**: Used for session management and security.
- **DATABASE_URL**: PostgreSQL connection string (e.g., `postgresql://postgres:your_password@localhost:5432/crm_db`).
- **FLASK_DEBUG**: Set to `1` to enable debug mode.
- **WhatsApp API Token** (Optional): Stored securely in the database (via the `settings` table) rather than `.env`. Only Admins can edit this via `/whatsapp_settings`. Used for sending reservation notifications and revenue reports to store WhatsApp numbers.
- **Public Routes**: No additional config needed, but ensure your CRM domain is accessible publicly for snippet integration. Customize CORS origins in app.py for security (replace '*' with specific store domains).

## Database Setup

1. **Install PostgreSQL**: Ensure PostgreSQL is installed and running on your system.
2. **Create the Database**:
   - Run the following command in your PostgreSQL client:
     ```sql
     CREATE DATABASE crm_db;
     ```
3. **Set Up Schema**:
   - The project uses raw SQL for database operations. You need to manually create the tables based on the models defined in `models/`. Below is the schema:
     ```sql
     CREATE TABLE users (
         id SERIAL PRIMARY KEY,
         username VARCHAR(50) UNIQUE NOT NULL,
         email VARCHAR(100) UNIQUE NOT NULL,
         password_hash VARCHAR(255) NOT NULL,
         user_level VARCHAR(20) DEFAULT 'Guest',
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     );

     CREATE TABLE stores (
         store_id SERIAL PRIMARY KEY,
         store_name VARCHAR(100) NOT NULL,
         store_telephone VARCHAR(20),
         store_email VARCHAR(100),
         store_address TEXT,
         store_whatsapp VARCHAR(20),
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         created_by INTEGER REFERENCES users(id),
         updated_by INTEGER REFERENCES users(id)
     );

     CREATE TABLE customers (
         customer_id SERIAL PRIMARY KEY,
         customer_name VARCHAR(100) NOT NULL,
         customer_code VARCHAR(50) UNIQUE,
         customer_is_member BOOLEAN DEFAULT FALSE,
         customer_organization VARCHAR(100),
         customer_telephone VARCHAR(20),
         customer_email VARCHAR(100),
         customer_address TEXT,
         customer_whatsapp VARCHAR(20),
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         created_by INTEGER REFERENCES users(id),
         updated_by INTEGER REFERENCES users(id)
     );

     CREATE TABLE store_customers (
         store_id INTEGER REFERENCES stores(store_id) ON DELETE CASCADE,
         customer_id INTEGER REFERENCES customers(customer_id) ON DELETE CASCADE,
         PRIMARY KEY (store_id, customer_id)
     );

     CREATE TABLE reservations (
         reservation_id SERIAL PRIMARY KEY,
         customer_id INTEGER REFERENCES customers(customer_id) ON DELETE CASCADE,
         store_id INTEGER REFERENCES stores(store_id) ON DELETE CASCADE,
         reservation_datetime TIMESTAMP NOT NULL,
         reservation_status VARCHAR(20) DEFAULT 'Pending',
         reservation_notes TEXT,
         reservation_event VARCHAR(100),
         reservation_room VARCHAR(50),
         reservation_guests INTEGER,
         reservation_code VARCHAR(20) UNIQUE,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         created_by INTEGER REFERENCES users(id),
         updated_by INTEGER REFERENCES users(id)
     );

     CREATE TABLE revenue_types (
         revenue_type_id SERIAL PRIMARY KEY,
         revenue_type_name VARCHAR(100) UNIQUE NOT NULL,
         revenue_type_category VARCHAR(20) NOT NULL CHECK (revenue_type_category IN ('Addition', 'Deduction')),
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         created_by INTEGER REFERENCES users(id),
         updated_by INTEGER REFERENCES users(id)
     );

     CREATE TABLE revenues (
         revenue_id SERIAL PRIMARY KEY,
         store_id INTEGER REFERENCES stores(store_id) ON DELETE CASCADE,
         revenue_date DATE NOT NULL,
         revenue_guests INTEGER,
         revenue_notes TEXT,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         created_by INTEGER REFERENCES users(id),
         updated_by INTEGER REFERENCES users(id)
     );

     CREATE TABLE revenue_items (
         revenue_item_id SERIAL PRIMARY KEY,
         revenue_id INTEGER REFERENCES revenues(revenue_id) ON DELETE CASCADE,
         revenue_type_id INTEGER REFERENCES revenue_types(revenue_type_id) ON DELETE RESTRICT,
         revenue_item_amount NUMERIC(15, 2) NOT NULL,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         created_by INTEGER REFERENCES users(id),
         updated_by INTEGER REFERENCES users(id)
     );

     CREATE TABLE revenue_compliments (
         revenue_compliment_id SERIAL PRIMARY KEY,
         revenue_id INTEGER REFERENCES revenues(revenue_id) ON DELETE CASCADE,
         revenue_compliment_description TEXT NOT NULL,
         revenue_compliment_for VARCHAR(100),
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         created_by INTEGER REFERENCES users(id),
         updated_by INTEGER REFERENCES users(id)
     );

     CREATE TABLE store_revenue_targets (
         target_id SERIAL PRIMARY KEY,
         store_id INTEGER NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
         target_month INTEGER NOT NULL CHECK (target_month >= 1 AND target_month <= 12),
         target_year INTEGER NOT NULL,
         target_amount NUMERIC(15, 2) NOT NULL,
         created_by INTEGER REFERENCES users(id),
         updated_by INTEGER REFERENCES users(id),
         created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
         -- Ensures each store has only one target per month/year
         UNIQUE (store_id, target_month, target_year)
     );

     CREATE TABLE settings (
         setting_key VARCHAR(255) PRIMARY KEY,
         setting_value TEXT,
         updated_at TIMESTAMPTZ DEFAULT NOW()
     );
     ```
4. **Create Initial Admin User**:
   - Since users registered via `/register` get the Guest role by default, you need to create an Admin user manually to access full functionality. First, generate a password hash using the following Python script:
     ```python
     from werkzeug.security import generate_password_hash
     password = "your_secure_password"  # Replace with your desired password
     print(generate_password_hash(password))
     ```
   - Then, insert the Admin user into the `users` table using the following SQL query in your PostgreSQL client:
     ```sql
     INSERT INTO users (username, email, password_hash, user_level, created_at, updated_at)
     VALUES (
         'admin',
         'admin@example.com',
         'your_password_hash_here',  -- Replace with the hash from the script above
         'Admin',
         CURRENT_TIMESTAMP,
         CURRENT_TIMESTAMP
     );
     ```
   - Alternatively, create a script `init_db.py` to automate this process (see [Project Structure](#project-structure) for adding it).

5. **Add Dummy Data**:
   - To populate the database with sample data for testing purposes, execute the following SQL commands in your PostgreSQL client after setting up the schema and Admin user:
     ```sql
     -- Data User (password: password123)
     INSERT INTO users (username, email, password_hash, user_level, created_at, updated_at)
     VALUES (
         'admin',
         'admin@example.com',
         'pbkdf2:sha256:600000$Mxpf6oFdnqK9Y8dt$fcfdae160ab84c44d85bdc5b2474a14df1826a427cbdbbcaa76051ce72402322',
         'Admin',
         CURRENT_TIMESTAMP,
         CURRENT_TIMESTAMP
     );

     -- Data Cabang Restoran (5 cabang)
     INSERT INTO stores (store_name, store_telephone, store_email, store_address, store_whatsapp, created_by, updated_by)
     VALUES
     ('Resto Citra', '+6212345678', 'citra@resto.id', 'Jl. Merdeka No.12, Jakarta', '+62812345678', 1, 1),
     ('Resto Harmoni', '+6223456789', 'harmoni@resto.id', 'Jl. Sudirman Kav. 21, Bandung', '+62823456789', 1, 1),
     ('Resto Nusantara', '+6234567890', 'nusantara@resto.id', 'Jl. Asia Afrika No. 88, Surabaya', '+62834567890', 1, 1),
     ('Resto Savory', '+6245678901', 'savory@resto.id', 'Jl. Pahlawan No. 45, Medan', '+62845678901', 1, 1),
     ('Resto Bahari', '+6256789012', 'bahari@resto.id', 'Jl. Pantai Kuta No. 77, Bali', '+62856789012', 1, 1);

     -- Data Pelanggan (5 pelanggan)
     INSERT INTO customers (customer_name, customer_code, customer_is_member, customer_telephone, customer_email, created_by, updated_by)
     VALUES
     ('Budi Santoso', 'CUST001', TRUE, '+62811223344', 'budi@gmail.com', 1, 1),
     ('Siti Rahayu', 'CUST002', FALSE, '+62822334455', 'siti@yahoo.co.id', 1, 1),
     ('Ahmad Wijaya', 'CUST003', TRUE, '+62833445566', 'ahmad@company.com', 1, 1),
     ('Dewi Lestari', 'CUST004', FALSE, '+62844556677', 'dewi.lestari@gmail.com', 1, 1),
     ('Rudi Hermawan', 'CUST005', TRUE, '+62855667788', 'rudi_hr@business.id', 1, 1);

     -- Relasi Cabang-Pelanggan (5 relasi)
     INSERT INTO store_customers (store_id, customer_id)
     VALUES
     (1, 1), (1, 2), (2, 3), (3, 4), (4, 5);

     -- Data Tipe Pendapatan (5 tipe)
     INSERT INTO revenue_types (revenue_type_name, revenue_type_category, created_by, updated_by)
     VALUES
     ('Food Sales', 'Addition', 1, 1),
     ('Beverage Sales', 'Addition', 1, 1),
     ('Service Charge', 'Addition', 1, 1),
     ('Employee Meal', 'Deduction', 1, 1),
     ('Complimentary', 'Deduction', 1, 1);

     -- Data Reservasi (5 reservasi)
     INSERT INTO reservations (customer_id, store_id, reservation_datetime, reservation_status, reservation_guests, reservation_code, created_by, updated_by)
     VALUES
     (1, 1, '2025-08-10 19:00:00', 'Confirmed', 4, 'RESV20250810001', 1, 1),
     (2, 1, '2025-08-11 20:00:00', 'Pending', 2, 'RESV20250811001', 1, 1),
     (3, 2, '2025-08-12 18:30:00', 'Confirmed', 6, 'RESV20250812001', 1, 1),
     (4, 3, '2025-08-13 21:00:00', 'Cancelled', 3, 'RESV20250813001', 1, 1),
     (5, 4, '2025-08-14 19:30:00', 'Confirmed', 5, 'RESV20250814001', 1, 1);

     -- Data Pendapatan (5 entri pendapatan)
     INSERT INTO revenues (store_id, revenue_date, revenue_guests, created_by, updated_by)
     VALUES
     (1, '2025-08-01', 120, 1, 1),
     (1, '2025-08-02', 95, 1, 1),
     (2, '2025-08-01', 80, 1, 1),
     (3, '2025-08-02', 65, 1, 1),
     (4, '2025-08-03', 110, 1, 1);

     -- Data Item Pendapatan (5 item)
     INSERT INTO revenue_items (revenue_id, revenue_type_id, revenue_item_amount, created_by, updated_by)
     VALUES
     (1, 1, 8500000.00, 1, 1),
     (1, 2, 3200000.00, 1, 1),
     (2, 1, 7200000.00, 1, 1),
     (3, 3, 1200000.00, 1, 1),
     (4, 1, 5500000.00, 1, 1);

     -- Data Komplimen (5 komplimen)
     INSERT INTO revenue_compliments (revenue_id, revenue_compliment_description, revenue_compliment_for, created_by, updated_by)
     VALUES
     (1, 'Dessert for birthday', 'Budi Santoso', 1, 1),
     (2, 'Welcome drink', 'New Customer', 1, 1),
     (3, 'Appetizer for VIP', 'Company Partner', 1, 1),
     (4, 'Coffee for complaint', 'Mrs. Dian', 1, 1),
     (5, 'Anniversary cake', 'Family Celebration', 1, 1);

     -- Dummy Data for Store Revenue Targets (Sample for 5 stores, August 2025)
     INSERT INTO store_revenue_targets (store_id, target_month, target_year, target_amount, created_by, updated_by)
     VALUES
     (1, 8, 2025, 10000000.00, 1, 1),
     (2, 8, 2025, 8000000.00, 1, 1),
     (3, 8, 2025, 7000000.00, 1, 1),
     (4, 8, 2025, 9000000.00, 1, 1),
     (5, 8, 2025, 12000000.00, 1, 1);

     -- Optional: Insert a sample WhatsApp API token (for testing; replace with your actual token)
     INSERT INTO settings (setting_key, setting_value)
     VALUES ('whatsapp_api_token', 'your_sample_fonnte_token_here');
     ```
   - Note: Ensure the Admin user (ID 1) exists before inserting dummy data, as it references `created_by` and `updated_by` fields. The WhatsApp token is optional and can be set via the app interface later.

6. **Run Migrations**:
   - Execute the SQL scripts above in your PostgreSQL client to set up the schema and populate the database with dummy data.

## Running the Application

Start the application with:
```bash
python app.py
```

The app will be accessible at `http://localhost:5000`.

## Testing

Currently, there are no automated tests. You can manually test the application by:
- Logging in and out.
- Performing CRUD operations on customers, stores, reservations, revenues, revenue types, and users (Admin role required for some actions).
- Associating customers with stores and vice versa.
- Creating, editing, and deleting reservations and revenue entries.
- Setting, viewing, editing, and deleting monthly revenue targets in store details.
- (Optional) Configuring the WhatsApp API token as an Admin, then testing the sending options in reservation forms and revenue detail pages (requires a valid token and store WhatsApp number).
- Public Reservation: Embed snippets in a test HTML page, submit a reservation, and check the public detail page. Verify CORS works and WhatsApp sends if enabled.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For inquiries, reach out to [211110108@student.mercubuana-yogya.ac.id](mailto:211110108@student.mercubuana-yogya.ac.id).