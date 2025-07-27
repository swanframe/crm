from models.base_model import BaseModel
import psycopg2.extras # Diperlukan untuk DictCursor di metode kustom
import math # Diperlukan untuk perhitungan pagination

class StoreCustomer(BaseModel):
    """
    Model untuk tabel penghubung store_customers (many-to-many).
    """
    _table_name = 'store_customers'
    # Primary key adalah kombinasi store_id dan customer_id,
    # jadi kita tidak menggunakan _primary_key tunggal di BaseModel.
    # Operasi CRUD untuk ini akan lebih spesifik.

    def __init__(self, store_id=None, customer_id=None):
        """
        Inisialisasi objek StoreCustomer.
        """
        super().__init__(
            store_id=store_id,
            customer_id=customer_id
        )

    def save(self):
        """
        Menyimpan relasi store-customer. Hanya INSERT yang relevan di sini.
        """
        conn = None
        cur = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            query = """
                INSERT INTO store_customers (store_id, customer_id)
                VALUES (%s, %s)
                ON CONFLICT (store_id, customer_id) DO NOTHING;
            """
            cur.execute(query, (self.store_id, self.customer_id))
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error saving store-customer relation: {e}")
            return False
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def delete(self):
        """
        Menghapus relasi store-customer.
        """
        conn = None
        cur = None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            query = """
                DELETE FROM store_customers
                WHERE store_id = %s AND customer_id = %s;
            """
            cur.execute(query, (self.store_id, self.customer_id))
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error deleting store-customer relation: {e}")
            return False
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    @classmethod
    def get_paginated_customers_for_store(cls, store_id, page, per_page):
        """
        Mengambil pelanggan yang terkait dengan toko tertentu dengan pagination.
        """
        offset = (page - 1) * per_page
        query = """
            SELECT c.* FROM customers c
            JOIN store_customers sc ON c.customer_id = sc.customer_id
            WHERE sc.store_id = %s
            ORDER BY c.customer_name ASC
            LIMIT %s OFFSET %s;
        """
        params = (store_id, per_page, offset)
        results = cls._execute_query(query, params, fetch_all=True)
        from models.customer import Customer # Import di sini untuk menghindari circular import
        return [Customer(**row) for row in results] if results else []

    @classmethod
    def count_customers_for_store(cls, store_id):
        """
        Menghitung total jumlah pelanggan yang terkait dengan toko tertentu.
        """
        query = """
            SELECT COUNT(*) FROM store_customers
            WHERE store_id = %s;
        """
        result = cls._execute_query(query, (store_id,), fetch_one=True)
        return result[0] if result else 0

    @classmethod
    def get_paginated_stores_for_customer(cls, customer_id, page, per_page):
        """
        Mengambil toko yang terkait dengan pelanggan tertentu dengan pagination.
        """
        offset = (page - 1) * per_page
        query = """
            SELECT s.* FROM stores s
            JOIN store_customers sc ON s.store_id = sc.store_id
            WHERE sc.customer_id = %s
            ORDER BY s.store_name ASC
            LIMIT %s OFFSET %s;
        """
        params = (customer_id, per_page, offset)
        results = cls._execute_query(query, params, fetch_all=True)
        from models.store import Store # Import di sini untuk menghindari circular import
        return [Store(**row) for row in results] if results else []

    @classmethod
    def count_stores_for_customer(cls, customer_id):
        """
        Menghitung total jumlah toko yang terkait dengan pelanggan tertentu.
        """
        query = """
            SELECT COUNT(*) FROM store_customers
            WHERE customer_id = %s;
        """
        result = cls._execute_query(query, (customer_id,), fetch_one=True)
        return result[0] if result else 0