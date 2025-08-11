# models/store_revenue_target.py
from models.base_model import BaseModel

class StoreRevenueTarget(BaseModel):
    """
    Model for the StoreRevenueTarget entity.
    Inherits basic CRUD functionality from BaseModel.
    This table stores monthly revenue targets for each store.
    """
    _table_name = 'store_revenue_targets'
    _primary_key = 'target_id'

    def __init__(self, target_id=None, store_id=None, target_month=None,
                 target_year=None, target_amount=None,
                 created_by=None, updated_by=None, created_at=None, updated_at=None):
        """
        Initializes a StoreRevenueTarget object.

        Args:
            target_id (int, optional): The unique ID of the revenue target.
            store_id (int, optional): Foreign Key to stores.store_id.
            target_month (int, optional): The month for the target (1-12).
            target_year (int, optional): The year for the target.
            target_amount (Decimal, optional): The target revenue amount.
            created_by (int, optional): ID of the user who created this record.
            updated_by (int, optional): ID of the user who last updated this record.
            created_at (datetime, optional): Timestamp of record creation.
            updated_at (datetime, optional): Timestamp of last record update.
        """
        super().__init__(
            target_id=target_id,
            store_id=store_id,
            target_month=target_month,
            target_year=target_year,
            target_amount=target_amount,
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at
        )

    @classmethod
    def find_by_store_and_date(cls, store_id, year, month):
        """
        Finds a specific revenue target for a given store, year, and month.
        """
        return cls.find_one_by(store_id=store_id, target_year=year, target_month=month)

    # Other custom methods can be added here as needed.
    # For example, a method to get all targets for a specific year.
    @classmethod
    def find_all_for_store_by_year(cls, store_id, year):
        """
        Finds all revenue targets for a given store for a specific year.
        """
        query = f"SELECT * FROM {cls._table_name} WHERE store_id = %s AND target_year = %s ORDER BY target_month ASC"
        results = cls._execute_query(query, (store_id, year), fetch_all=True)
        return [cls(**row) for row in results] if results else []