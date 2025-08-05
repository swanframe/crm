# models/revenue_type.py
from models.base_model import BaseModel

class RevenueType(BaseModel):
    """
    Model for the RevenueType entity.
    Inherits basic CRUD functionality from BaseModel.
    This table defines dynamic types for revenue additions and deductions.
    """
    _table_name = 'revenue_types'
    _primary_key = 'revenue_type_id'

    def __init__(self, revenue_type_id=None, revenue_type_name=None, revenue_type_category=None,
                 created_by=None, updated_by=None, created_at=None, updated_at=None):
        """
        Initializes a RevenueType object.
        Args:
            revenue_type_id (int, optional): The unique ID of the revenue type.
            revenue_type_name (str, optional): The name of the revenue type (e.g., 'Cash', 'Commission').
            revenue_type_category (str, optional): The category of the revenue type ('Addition' or 'Deduction').
            created_by (int, optional): ID of the user who created this record.
            updated_by (int, optional): ID of the user who last updated this record.
            created_at (datetime, optional): Timestamp of record creation.
            updated_at (datetime, optional): Timestamp of last record update.
        """
        super().__init__(
            revenue_type_id=revenue_type_id,
            revenue_type_name=revenue_type_name,
            revenue_type_category=revenue_type_category,
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at
        )

    # No specific methods needed here as BaseModel handles basic CRUD.
    # Validation for revenue_type_category ('Addition', 'Deduction') is handled by DB constraint.