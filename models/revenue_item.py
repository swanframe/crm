# models/revenue_item.py
from models.base_model import BaseModel
# Import Revenue and RevenueType models locally when needed
# from models.revenue import Revenue
# from models.revenue_type import RevenueType

class RevenueItem(BaseModel):
    """
    Model for the RevenueItem entity.
    Inherits basic CRUD functionality from BaseModel.
    This table stores individual addition/deduction items for a revenue entry.
    """
    _table_name = 'revenue_items'
    _primary_key = 'revenue_item_id'

    def __init__(self, revenue_item_id=None, revenue_id=None, revenue_type_id=None,
                 revenue_item_amount=None,
                 created_by=None, updated_by=None, created_at=None, updated_at=None):
        """
        Initializes a RevenueItem object.
        Args:
            revenue_item_id (int, optional): The unique ID of the revenue item.
            revenue_id (int, optional): Foreign Key to revenues.revenue_id.
            revenue_type_id (int, optional): Foreign Key to revenue_types.revenue_type_id.
            revenue_item_amount (float, optional): The amount for this revenue item.
            created_by (int, optional): ID of the user who created this record.
            updated_by (int, optional): ID of the user who last updated this record.
            created_at (datetime, optional): Timestamp of record creation.
            updated_at (datetime, optional): Timestamp of last record update.
        """
        super().__init__(
            revenue_item_id=revenue_item_id,
            revenue_id=revenue_id,
            revenue_type_id=revenue_type_id,
            revenue_item_amount=revenue_item_amount,
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at
        )

    def get_revenue_type_details(self):
        """
        Fetches the full RevenueType object for the associated revenue type.
        """
        from models.revenue_type import RevenueType # Local import
        revenue_type = RevenueType.find_by_id(self.revenue_type_id)
        return revenue_type

    def get_revenue_type_name(self):
        """
        Fetches the name of the associated revenue type.
        """
        revenue_type = self.get_revenue_type_details()
        return revenue_type.revenue_type_name if revenue_type else "N/A"

    def get_revenue_type_category(self):
        """
        Fetches the category of the associated revenue type ('Addition' or 'Deduction').
        """
        revenue_type = self.get_revenue_type_details()
        return revenue_type.revenue_type_category if revenue_type else "N/A"