# models/customer.py
from models.base_model import BaseModel

class Customer(BaseModel):
    """
    Model untuk entitas Customer.
    Mewarisi fungsionalitas CRUD dasar dari BaseModel.
    """
    _table_name = 'customers'
    _primary_key = 'customer_id'

    def __init__(self, customer_id=None, customer_name=None, customer_code=None, customer_is_member=False, # <-- Ubah nama atribut
                 customer_organization=None, customer_telephone=None, customer_email=None, customer_address=None, customer_whatsapp=None, # <-- Ubah nama atribut
                 created_by=None, updated_by=None, created_at=None, updated_at=None):
        """
        Inisialisasi objek Customer.
        Menambahkan customer_code, customer_organization, customer_telephone, customer_email, customer_address, dan customer_whatsapp sebagai atribut opsional.
        """
        super().__init__(
            customer_id=customer_id,
            customer_name=customer_name,
            customer_code=customer_code,
            customer_is_member=customer_is_member, # <-- Inisialisasi atribut baru
            customer_organization=customer_organization, # <-- Inisialisasi atribut baru
            customer_telephone=customer_telephone, 
            customer_email=customer_email,         
            customer_address=customer_address,     
            customer_whatsapp=customer_whatsapp,   
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at
        )