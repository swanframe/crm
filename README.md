# CRM System

A simple Customer Relationship Management (CRM) system built with Flask and PostgreSQL. This project allows users to manage customers, stores, user accounts, reservations, and now includes revenue management. It features role-based access control, multi-language support, and a many-to-many relationship between stores and customers.

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
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
- **Many-to-Many Relationship**: Manage associations between stores and customers.
- **User Profile and Settings**: View profile and update password.
- **Multi-Language Support**: Available in English, Indonesian, and Chinese.
- **Secure Password Hashing**: Uses Werkzeug for password security.

## Project Structure

Below is the structure of the project directory:

```
crm/
├── app.py                  # Main application entry point
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
│   └── revenue_compliment.py # Revenue Compliment model
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
│   └── revenue_detail.html # Revenue detail page
├── utilities/
│   ├── security.py         # Password hashing utilities
│   └── localization.py     # Multi-language translation utilities
└── translations/
    ├── en.json             # English translations
    ├── id.json             # Indonesian translations
    └── zh.json             # Chinese translations
```

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
- **Manage Reservations**: Go to `/reservations` to perform CRUD operations on reservations (requires Admin, Operator, or Contributor role).
- **Manage Revenues**: Go to `/revenues` to perform CRUD operations on revenue entries (requires Admin, Operator, or Contributor role).
- **Manage Revenue Types**: Go to `/revenue_types` to perform CRUD operations on revenue types (requires Admin or Operator role).
- **Manage Users**: Admins can manage users at `/users`.
- **Profile and Settings**: Access `/profile` and `/settings` for user account management.

## Configuration

Configuration is managed through `config.py` and environment variables:

- **SECRET_KEY**: Used for session management and security.
- **DATABASE_URL**: PostgreSQL connection string (e.g., `postgresql://postgres:your_password@localhost:5432/crm_db`).
- **FLASK_DEBUG**: Set to `1` to enable debug mode.

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

5. **Run Migrations**: Execute the SQL scripts above in your PostgreSQL client.

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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For inquiries, reach out to [211110108@student.mercubuana-yogya.ac.id](mailto:211110108@student.mercubuana-yogya.ac.id).
