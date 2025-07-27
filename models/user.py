# models/user.py
from models.base_model import BaseModel
from utilities.security import hash_password, check_hashed_password
import psycopg2.extras

class User(BaseModel):
    """
    Model untuk entitas User.
    Mewarisi fungsionalitas CRUD dasar dari BaseModel.
    """
    _table_name = 'users'
    _primary_key = 'id'

    def __init__(self, id=None, username=None, email=None, password_hash=None,
                 user_level='Guest', # Menambahkan atribut user_level dengan default 'Guest'
                 created_at=None, updated_at=None):
        """
        Inisialisasi objek User.
        """
        super().__init__(
            id=id,
            username=username,
            email=email,
            password_hash=password_hash,
            user_level=user_level, # Meneruskan user_level ke BaseModel
            created_at=created_at,
            updated_at=updated_at
        )

    @classmethod
    def create_new_user(cls, username, email, password, user_level='Guest'): # Menambahkan parameter user_level
        """
        Membuat user baru dengan menghash password dan menetapkan level.
        Mengembalikan instance User jika berhasil, None jika gagal (misal: username/email sudah ada).
        """
        hashed_pwd = hash_password(password)
        
        # Cek apakah username atau email sudah ada
        if cls.find_one_by(username=username) or cls.find_one_by(email=email):
            return None # User dengan username atau email ini sudah ada

        conn = None
        cur = None
        try:
            conn = cls._get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 
            query = """
                INSERT INTO users (username, email, password_hash, user_level)
                VALUES (%s, %s, %s, %s) RETURNING id, username, email, password_hash, user_level, created_at, updated_at
            """
            cur.execute(query, (username, email, hashed_pwd, user_level)) # Menambahkan user_level ke query INSERT
            conn.commit()
            result = cur.fetchone()
            return cls(**result) if result else None
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error creating new user: {e}")
            return None
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def update_password(self, new_password):
        """
        Memperbarui password hash pengguna.
        """
        new_password_hash = hash_password(new_password)
        self.password_hash = new_password_hash
        # Panggil metode save dari BaseModel untuk menyimpan perubahan ke DB
        return self.save(self.id) # Gunakan ID user sebagai updated_by