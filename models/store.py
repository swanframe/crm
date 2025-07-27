from models.base_model import BaseModel

class Store(BaseModel):
    """
    Model untuk entitas Store.
    Mewarisi fungsionalitas CRUD dasar dari BaseModel.
    """
    _table_name = 'stores'
    _primary_key = 'store_id'

    def __init__(self, store_id=None, store_name=None, store_telephone=None, store_email=None, store_address=None, store_whatsapp=None, # <-- Ubah nama atribut
                 created_by=None, updated_by=None, created_at=None, updated_at=None):
        """
        Inisialisasi objek Store.
        Menambahkan store_telephone, store_email, store_address, dan store_whatsapp sebagai atribut opsional.
        """
        super().__init__(
            store_id=store_id,
            store_name=store_name,
            store_telephone=store_telephone, # <-- Inisialisasi atribut baru
            store_email=store_email,         # <-- Inisialisasi atribut baru
            store_address=store_address,     # <-- Inisialisasi atribut baru
            store_whatsapp=store_whatsapp,   # <-- Inisialisasi atribut baru
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at
        )