# models/revenue_compliment.py
from models.base_model import BaseModel
# Import Revenue model locally when needed
# from models.revenue import Revenue

class RevenueCompliment(BaseModel):
    """
    Model for the RevenueCompliment entity.
    Inherits basic CRUD functionality from BaseModel.
    This table stores compliment entries related to a revenue, which do not affect total revenue.
    """
    _table_name = 'revenue_compliments'
    _primary_key = 'revenue_compliment_id'

    def __init__(self, revenue_compliment_id=None, revenue_id=None,
                 revenue_compliment_description=None, revenue_compliment_for=None,
                 created_by=None, updated_by=None, created_at=None, updated_at=None):
        """
        Initializes a RevenueCompliment object.
        Args:
            revenue_compliment_id (int, optional): The unique ID of the compliment.
            revenue_id (int, optional): Foreign Key to revenues.revenue_id.
            revenue_compliment_description (str, optional): Short description of the compliment.
            revenue_compliment_for (str, optional): Who the compliment was given for.
            created_by (int, optional): ID of the user who created this record.
            updated_by (int, optional): ID of the user who last updated this record.
            created_at (datetime, optional): Timestamp of record creation.
            updated_at (datetime, optional): Timestamp of last record update.
        """
        super().__init__(
            revenue_compliment_id=revenue_compliment_id,
            revenue_id=revenue_id,
            revenue_compliment_description=revenue_compliment_description,
            revenue_compliment_for=revenue_compliment_for,
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at
        )

    # No specific methods needed here as BaseModel handles basic CRUD.