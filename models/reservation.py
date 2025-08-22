# models/reservation.py
import datetime
import random
import string
from models.base_model import BaseModel

class Reservation(BaseModel):
    """
    Model for the Reservation entity.
    Inherits basic CRUD functionality from BaseModel.
    """
    _table_name = 'reservations'
    _primary_key = 'reservation_id'

    def __init__(self, reservation_id=None, customer_id=None, store_id=None,
                 reservation_datetime=None, reservation_status='Pending',
                 reservation_notes=None,
                 reservation_event=None, reservation_room=None, reservation_guests=None,
                 reservation_code=None, # NEW: Add reservation_code attribute
                 created_by=None, updated_by=None,
                 created_at=None, updated_at=None):
        """
        Initializes a Reservation object.
        """
        super().__init__(
            reservation_id=reservation_id,
            customer_id=customer_id,
            store_id=store_id,
            reservation_datetime=reservation_datetime,
            reservation_status=reservation_status,
            reservation_notes=reservation_notes,
            reservation_event=reservation_event,
            reservation_room=reservation_room,
            reservation_guests=reservation_guests,
            reservation_code=reservation_code, # NEW: Initialize reservation_code
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at
        )

    @staticmethod
    def generate_reservation_code(reservation_date): # MODIFIED: Accepts reservation_date
        """
        Generates a 10-character reservation code:
        - First 4 digits: random uppercase letters (A-Z)
        - Next 2 digits: day (DD) from reservation_date
        - Next 2 digits: month (MM) from reservation_date
        - Last 2 digits: year (YY) from reservation_date
        Example: ABCD280825 (if reservation_date is 28 August 2025)
        """
        # Generate 4 random uppercase letters
        random_letters = ''.join(random.choices(string.ascii_uppercase, k=4))
        
        # Get date components from the provided reservation_date
        day = reservation_date.strftime('%d') # Day as 2 digits
        month = reservation_date.strftime('%m') # Month as 2 digits
        year = reservation_date.strftime('%y') # Year as 2 digits (last two digits)

        return f"{random_letters}{day}{month}{year}"

    def save(self, user_id=None):
        """
        Saves or updates the record in the database.
        If primary key exists, performs UPDATE; otherwise, performs INSERT.
        Updates created_at, updated_at.
        If the table has created_by/updated_by, they will also be filled.
        Returns True on success, False on failure (including UniqueViolation).
        Generates reservation_code if it's a new record and not provided.
        """
        if not self._table_name:
            raise NotImplementedError("Table name not set for this model.")

        pk_value = getattr(self, self._primary_key, None)
        current_time = datetime.datetime.now()

        # Check if the table has created_by/updated_by columns
        has_created_by = hasattr(self, 'created_by')
        has_updated_by = hasattr(self, 'updated_by')

        result = None
        if pk_value: # If primary key exists, perform UPDATE
            set_clauses = []
            params = []
            for key, value in self.__dict__.items():
                # Do not update primary key, created_at, created_by, updated_at, updated_by
                # updated_at and updated_by columns will be added explicitly
                if key != self._primary_key and key not in ['created_at', 'created_by', 'updated_at', 'updated_by', '_last_error']:
                    set_clauses.append(f"{key} = %s")
                    params.append(value)
            
            # Add updated_at explicitly (only once)
            set_clauses.append("updated_at = %s")
            params.append(current_time)

            # Add updated_by explicitly if it exists and user_id is provided (only once)
            if has_updated_by and user_id is not None:
                set_clauses.append("updated_by = %s")
                params.append(user_id)

            params.append(pk_value) # Add primary key value for WHERE clause

            query = f"UPDATE {self._table_name} SET {', '.join(set_clauses)} WHERE {self._primary_key} = %s RETURNING *"
            result = self._execute_query(query, tuple(params), fetch_one=True, commit=True)
        else: # If primary key does not exist, perform INSERT
            columns = []
            placeholders = []
            params = []

            # Generate reservation_code if it's a new record and not already set
            # MODIFIED: Pass self.reservation_datetime to generate_reservation_code
            if not self.reservation_code and self.reservation_datetime:
                self.reservation_code = self.generate_reservation_code(self.reservation_datetime)
            elif not self.reservation_code and not self.reservation_datetime:
                # Handle case where reservation_datetime is not set (e.g., validation failed earlier)
                # You might want to raise an error or assign a default/placeholder code
                # For now, we'll leave it as None if reservation_datetime is missing
                self.reservation_code = None


            # Set created_at and updated_at
            self.created_at = current_time
            self.updated_at = current_time
            
            # Set created_by and updated_by if they exist and user_id is provided
            if has_created_by and user_id is not None:
                self.created_by = user_id
                self.updated_by = user_id

            for key, value in self.__dict__.items():
                # Do not include primary key if SERIAL and no value is set
                # Only include columns that have a value in the instance
                if key != self._primary_key and key != '_last_error' or (key == self._primary_key and value is not None):
                    columns.append(key)
                    placeholders.append('%s')
                    params.append(value)

            query = f"INSERT INTO {self._table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING *"
            result = self._execute_query(query, tuple(params), fetch_one=True, commit=True)
        
        # Check if result is a string (indicating an error)
        if isinstance(result, str) and result.startswith("duplicate_key_error:"):
            self._last_error = result # Store the error message
            return False
        elif result:
            for key, value in result.items():
                setattr(self, key, value) # Update instance attributes with newly saved/updated data
            self._last_error = None # Clear previous error if successful
            return True
        self._last_error = "Unknown error during save." # General error message if no result
        return False

    def get_customer_name(self):
        """
        Fetches the name of the associated customer.
        """
        from models.customer import Customer # Local import to avoid circular dependency
        customer = Customer.find_by_id(self.customer_id)
        return customer.customer_name if customer else "N/A"

    def get_customer_details(self):
        """
        Fetches the full Customer object for the associated customer.
        """
        from models.customer import Customer # Local import to avoid circular dependency
        customer = Customer.find_by_id(self.customer_id)
        return customer

    def get_store_name(self):
        """
        Fetches the name of the associated store.
        """
        from models.store import Store # Local import to avoid circular dependency
        store = Store.find_by_id(self.store_id)
        return store.store_name if store else "N/A"

    @classmethod
    def get_paginated_data(cls, page, per_page, search_query=None, search_columns=None, sort_by=None, sort_order='asc'):
        """
        Fetches reservation data with pagination, search, and sorting,
        including searching by customer name and store name.
        """
        # Define JOIN clauses and columns for searching in joined tables
        join_tables = [
            "JOIN customers c ON t.customer_id = c.customer_id",
            "JOIN stores s ON t.store_id = s.store_id"
        ]
        join_columns_for_search = {
            'customer_name': 'c.customer_name',
            'store_name': 's.store_name',
            'reservation_guests': 't.reservation_guests'
        }
        
        # Combine base search columns with joined columns
        all_search_columns = search_columns + list(join_columns_for_search.keys()) if search_columns else list(join_columns_for_search.keys())

        return super().get_paginated_data(
            page, per_page, search_query, all_search_columns, sort_by, sort_order,
            join_tables=join_tables, join_columns_for_search=join_columns_for_search
        )

    @classmethod
    def count_all(cls, search_query=None, search_columns=None):
        """
        Counts the total number of reservation records, with search options,
        including searching by customer name and store name.
        """
        join_tables = [
            "JOIN customers c ON t.customer_id = c.customer_id",
            "JOIN stores s ON t.store_id = s.store_id"
        ]
        join_columns_for_search = {
            'customer_name': 'c.customer_name',
            'store_name': 's.store_name',
            'reservation_guests': 't.reservation_guests'
        }

        all_search_columns = search_columns + list(join_columns_for_search.keys()) if search_columns else list(join_columns_for_search.keys())

        return super().count_all(
            search_query, all_search_columns,
            join_tables=join_tables, join_columns_for_search=join_columns_for_search
        )

    @classmethod
    def get_reservations_by_store_and_date_range(cls, store_id, start_date, end_date, limit=30):
        """
        Mendapatkan daftar reservasi untuk toko tertentu dalam rentang tanggal
        """
        query = """
            SELECT * FROM reservations 
            WHERE store_id = %s 
            AND reservation_datetime::date BETWEEN %s AND %s
            ORDER BY reservation_datetime ASC
            LIMIT %s
        """
        params = (store_id, start_date, end_date, limit)
        
        results = cls._execute_query(query, params, fetch_all=True)
        return [cls(**row) for row in results] if results else []