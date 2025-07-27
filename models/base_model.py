import psycopg2
from psycopg2 import extras
from psycopg2 import errors # Import errors module
from config import Config
import datetime

class BaseModel:
    """
    Kelas dasar untuk semua model database.
    Menyediakan fungsionalitas umum untuk koneksi database dan operasi CRUD.
    """
    _db_url = Config.DATABASE_URL
    _table_name = None # Harus di-override oleh kelas turunan
    _primary_key = 'id' # Kolom primary key default

    def __init__(self, **kwargs):
        """
        Inisialisasi instance model dengan atribut yang diberikan.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._last_error = None # Tambahkan atribut untuk menyimpan pesan error terakhir

    @classmethod
    def _get_connection(cls):
        """
        Membuat dan mengembalikan koneksi database.
        """
        try:
            conn = psycopg2.connect(cls._db_url)
            return conn
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise

    @classmethod
    def _execute_query(cls, query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """
        Menjalankan query SQL dan mengembalikan hasilnya.
        Jika commit=True, akan mengembalikan hasil fetch_one jika diminta,
        atau True jika hanya commit tanpa fetch.
        Mengembalikan string error yang spesifik jika terjadi UniqueViolation.
        """
        conn = None
        cur = None
        try:
            conn = cls._get_connection()
            cur = conn.cursor(cursor_factory=extras.DictCursor) # Menggunakan DictCursor untuk hasil seperti dict
            cur.execute(query, params)

            result = None
            if fetch_one:
                result = cur.fetchone()
            elif fetch_all:
                result = cur.fetchall()

            if commit:
                conn.commit()
                return result if (fetch_one or fetch_all) else True # Mengembalikan hasil fetch jika ada, atau True
            else:
                return result
        except errors.UniqueViolation as e: # Tangkap spesifik UniqueViolation
            if conn:
                conn.rollback() # Rollback jika ada error
            print(f"Database unique constraint error: {e}")
            # Mengembalikan string error yang lebih spesifik untuk ditangani di lapisan aplikasi
            return f"duplicate_key_error:{e.diag.constraint_name}:{e.diag.message_detail}"
        except Exception as e:
            if conn:
                conn.rollback() # Rollback jika ada error
            print(f"Database query error: {e}")
            raise # Re-raise exception for other errors
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    @classmethod
    def find_by_id(cls, item_id):
        """
        Mencari record berdasarkan primary key.
        """
        if not cls._table_name:
            raise NotImplementedError("Table name not set for this model.")
        query = f"SELECT * FROM {cls._table_name} WHERE {cls._primary_key} = %s"
        result = cls._execute_query(query, (item_id,), fetch_one=True)
        # Pastikan result bukan string error sebelum membuat instance
        if isinstance(result, str) and result.startswith("duplicate_key_error:"):
            return None # Atau tangani sesuai kebutuhan, tapi untuk find_by_id ini tidak diharapkan
        return cls(**result) if result else None

    @classmethod
    def find_one_by(cls, **kwargs):
        """
        Mencari satu record berdasarkan kriteria tertentu.
        Contoh: User.find_one_by(username='john_doe')
        """
        if not cls._table_name:
            raise NotImplementedError("Table name not set for this model.")
        
        conditions = [f"{key} = %s" for key in kwargs.keys()]
        query = f"SELECT * FROM {cls._table_name} WHERE {' AND '.join(conditions)}"
        params = tuple(kwargs.values())
        result = cls._execute_query(query, params, fetch_one=True)
        # Pastikan result bukan string error sebelum membuat instance
        if isinstance(result, str) and result.startswith("duplicate_key_error:"):
            return None # Atau tangani sesuai kebutuhan
        return cls(**result) if result else None

    @classmethod
    def find_all(cls):
        """
        Mengambil semua record dari tabel.
        """
        if not cls._table_name:
            raise NotImplementedError("Table name not set for this model.")
        query = f"SELECT * FROM {cls._table_name}"
        results = cls._execute_query(query, fetch_all=True)
        # Pastikan results bukan string error sebelum membuat instance
        if isinstance(results, str) and results.startswith("duplicate_key_error:"):
            return [] # Atau tangani sesuai kebutuhan
        return [cls(**row) for row in results] if results else []

    @classmethod
    def get_paginated_data(cls, page, per_page, search_query=None, search_columns=None, sort_by=None, sort_order='asc'):
        """
        Mengambil data dengan pagination, pencarian, dan penyortiran.
        Args:
            page (int): Nomor halaman saat ini (dimulai dari 1).
            per_page (int): Jumlah item per halaman.
            search_query (str, optional): String pencarian. Defaults to None.
            search_columns (list, optional): Daftar kolom yang akan dicari. Defaults to None.
            sort_by (str, optional): Nama kolom untuk menyortir. Defaults to None.
            sort_order (str, optional): Arah penyortiran ('asc' atau 'desc'). Defaults to 'asc'.
        Returns:
            list: Daftar objek model.
        """
        if not cls._table_name:
            raise NotImplementedError("Table name not set for this model.")

        offset = (page - 1) * per_page
        query_parts = [f"SELECT * FROM {cls._table_name}"]
        params = []

        if search_query and search_columns:
            search_conditions = []
            for col in search_columns:
                search_conditions.append(f"{col} ILIKE %s") # ILIKE untuk case-insensitive
                params.append(f"%{search_query}%")
            query_parts.append(f"WHERE {' OR '.join(search_conditions)}")
        
        # Tambahkan ORDER BY clause
        order_clause = ""
        if sort_by:
            # Pastikan sort_by adalah kolom yang valid untuk menghindari SQL injection
            # Untuk demo ini, kita asumsikan sort_by adalah nama kolom yang aman
            # Dalam produksi, Anda harus memvalidasi ini terhadap daftar kolom yang diizinkan
            if sort_order.lower() not in ['asc', 'desc']:
                sort_order = 'asc' # Default ke asc jika order tidak valid
            order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
        else:
            # Default sort jika tidak ada sort_by yang diberikan
            order_clause = f"ORDER BY {cls._primary_key} ASC"

        query_parts.append(order_clause)
        query_parts.append(f"LIMIT %s OFFSET %s")
        params.extend([per_page, offset])

        query = " ".join(query_parts)
        results = cls._execute_query(query, tuple(params), fetch_all=True)
        # Handle the case where _execute_query returns a string error
        if isinstance(results, str) and results.startswith("duplicate_key_error:"):
            return [] # Untuk SELECT, ini tidak diharapkan, tapi untuk keamanan
        return [cls(**row) for row in results] if results else []

    @classmethod
    def count_all(cls, search_query=None, search_columns=None):
        """
        Menghitung total jumlah record, dengan opsi pencarian.
        Args:
            search_query (str, optional): String pencarian. Defaults to None.
            search_columns (list, optional): Daftar kolom yang akan dicari. Defaults to None.
        Returns:
            int: Total jumlah record.
        """
        if not cls._table_name:
            raise NotImplementedError("Table name not set for this model.")
        
        query_parts = [f"SELECT COUNT(*) FROM {cls._table_name}"]
        params = []

        if search_query and search_columns:
            search_conditions = []
            for col in search_columns:
                search_conditions.append(f"{col} ILIKE %s")
                params.append(f"%{search_query}%")
            query_parts.append(f"WHERE {' OR '.join(search_conditions)}")
        
        query = " ".join(query_parts)
        result = cls._execute_query(query, tuple(params), fetch_one=True)
        # Handle the case where _execute_query returns a string error
        if isinstance(result, str) and result.startswith("duplicate_key_error:"):
            return 0 # Untuk SELECT, ini tidak diharapkan, tapi untuk keamanan
        return result[0] if result else 0

    def save(self, user_id=None): # user_id sekarang opsional
        """
        Menyimpan atau memperbarui record di database.
        Jika primary key ada, lakukan UPDATE; jika tidak, lakukan INSERT.
        Memperbarui created_at, updated_at.
        Jika tabel memiliki created_by/updated_by, juga akan diisi.
        Mengembalikan True jika berhasil, False jika gagal (termasuk UniqueViolation).
        """
        if not self._table_name:
            raise NotImplementedError("Table name not set for this model.")

        pk_value = getattr(self, self._primary_key, None)
        current_time = datetime.datetime.now()

        # Cek apakah tabel memiliki kolom created_by/updated_by
        has_created_by = hasattr(self, 'created_by')
        has_updated_by = hasattr(self, 'updated_by')

        result = None
        if pk_value: # Jika primary key ada, lakukan UPDATE
            set_clauses = []
            params = []
            for key, value in self.__dict__.items():
                # Jangan update primary key, created_at, created_by, updated_at, updated_by
                # Kolom updated_at dan updated_by akan ditambahkan secara eksplisit
                if key != self._primary_key and key not in ['created_at', 'created_by', 'updated_at', 'updated_by', '_last_error']:
                    set_clauses.append(f"{key} = %s")
                    params.append(value)
            
            # Tambahkan updated_at secara eksplisit (hanya sekali)
            set_clauses.append("updated_at = %s")
            params.append(current_time)

            # Tambahkan updated_by secara eksplisit jika ada dan user_id disediakan (hanya sekali)
            if has_updated_by and user_id is not None:
                set_clauses.append("updated_by = %s")
                params.append(user_id)

            params.append(pk_value) # Tambahkan nilai primary key untuk WHERE clause

            query = f"UPDATE {self._table_name} SET {', '.join(set_clauses)} WHERE {self._primary_key} = %s RETURNING *"
            result = self._execute_query(query, tuple(params), fetch_one=True, commit=True)
        else: # Jika primary key tidak ada, lakukan INSERT
            columns = []
            placeholders = []
            params = []

            # Set created_at dan updated_at
            self.created_at = current_time
            self.updated_at = current_time
            
            # Set created_by dan updated_by jika ada dan user_id disediakan
            if has_created_by and user_id is not None:
                self.created_by = user_id
                self.updated_by = user_id

            for key, value in self.__dict__.items():
                # Jangan masukkan primary key jika SERIAL dan belum ada nilainya
                # Kita hanya masukkan kolom yang memiliki nilai di instance
                if key != self._primary_key and key != '_last_error' or (key == self._primary_key and value is not None):
                    columns.append(key)
                    placeholders.append('%s')
                    params.append(value)

            query = f"INSERT INTO {self._table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING *"
            result = self._execute_query(query, tuple(params), fetch_one=True, commit=True)
        
        # Periksa apakah result adalah string (menunjukkan error)
        if isinstance(result, str) and result.startswith("duplicate_key_error:"):
            self._last_error = result # Simpan pesan error
            return False
        elif result:
            for key, value in result.items():
                setattr(self, key, value) # Perbarui atribut instance dengan data yang baru disimpan/diperbarui
            self._last_error = None # Hapus error sebelumnya jika berhasil
            return True
        self._last_error = "Unknown error during save." # Pesan error umum jika tidak ada hasil
        return False

    def delete(self):
        """
        Menghapus record dari database berdasarkan primary key.
        """
        if not self._table_name:
            raise NotImplementedError("Table name not set for this model.")
        
        pk_value = getattr(self, self._primary_key, None)
        if not pk_value:
            raise ValueError("Cannot delete unsaved record (no primary key).")

        query = f"DELETE FROM {self._table_name} WHERE {self._primary_key} = %s"
        result = self._execute_query(query, (pk_value,), commit=True)
        # Periksa apakah result adalah string (menunjukkan error)
        if isinstance(result, str) and result.startswith("duplicate_key_error:"):
            self._last_error = result # Simpan pesan error
            return False
        self._last_error = None # Hapus error sebelumnya jika berhasil
        return result # Akan True jika berhasil, atau False jika error lain

    def get_last_error(self):
        """
        Mengembalikan pesan error terakhir dari operasi save/delete.
        """
        return getattr(self, '_last_error', None)