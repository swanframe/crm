# models/revenue.py
import datetime
from models.base_model import BaseModel
# Import Store model locally when needed to avoid circular dependencies
# from models.store import Store

class Revenue(BaseModel):
    """
    Model for the Revenue entity.
    Inherits basic CRUD functionality from BaseModel.
    This table stores main revenue entries linked to a specific store.
    """
    _table_name = 'revenues'
    _primary_key = 'revenue_id'

    def __init__(self, revenue_id=None, store_id=None, revenue_date=None,
                 revenue_guests=None, revenue_notes=None,
                 created_by=None, updated_by=None, created_at=None, updated_at=None):
        """
        Initializes a Revenue object.
        Args:
            revenue_id (int, optional): The unique ID of the revenue entry.
            store_id (int, optional): Foreign Key to stores.store_id.
            revenue_date (date, optional): The date of the revenue.
            revenue_guests (int, optional): Number of guests for this revenue entry.
            revenue_notes (str, optional): General notes for this revenue entry.
            created_by (int, optional): ID of the user who created this record.
            updated_by (int, optional): ID of the user who last updated this record.
            created_at (datetime, optional): Timestamp of record creation.
            updated_at (datetime, optional): Timestamp of last record update.
        """
        super().__init__(
            revenue_id=revenue_id,
            store_id=store_id,
            revenue_date=revenue_date,
            revenue_guests=revenue_guests,
            revenue_notes=revenue_notes,
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at
        )

    def get_store_name(self):
        """
        Fetches the name of the associated store.
        """
        from models.store import Store # Local import to avoid circular dependency
        store = Store.find_by_id(self.store_id)
        return store.store_name if store else "N/A"

    def get_store_details(self):
        """
        Fetches the full Store object for the associated store.
        """
        from models.store import Store # Local import to avoid circular dependency
        store = Store.find_by_id(self.store_id)
        return store

    @classmethod
    def get_paginated_data(cls, page, per_page, search_query=None, search_columns=None, sort_by=None, sort_order='asc'):
        """
        Fetches revenue data with pagination, search, and sorting,
        including searching by store name.
        """
        # Define JOIN clauses and columns for searching in joined tables
        join_tables = [
            "JOIN stores s ON t.store_id = s.store_id"
        ]
        join_columns_for_search = {
            'store_name': 's.store_name'
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
        Counts the total number of revenue records, with search options,
        including searching by store name.
        """
        join_tables = [
            "JOIN stores s ON t.store_id = s.store_id"
        ]
        join_columns_for_search = {
            'store_name': 's.store_name'
        }

        all_search_columns = search_columns + list(join_columns_for_search.keys()) if search_columns else list(join_columns_for_search.keys())

        return super().count_all(
            search_query, all_search_columns,
            join_tables=join_tables, join_columns_for_search=join_columns_for_search
        )

    @classmethod
    def get_monthly_net_revenue(cls, store_id, year, month):
        """Menghitung total pendapatan bersih untuk bulan tertentu"""
        start_date = datetime.date(year, month, 1)
        if month == 12:
            end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        
        query = """
            SELECT COALESCE(SUM(net_amount), 0) as total_net
            FROM (
                SELECT 
                    r.revenue_id,
                    (COALESCE(SUM(CASE WHEN rt.revenue_type_category = 'Addition' THEN ri.revenue_item_amount ELSE 0 END), 0) 
                     - COALESCE(SUM(CASE WHEN rt.revenue_type_category = 'Deduction' THEN ri.revenue_item_amount ELSE 0 END), 0)
                    ) as net_amount
                FROM revenues r
                LEFT JOIN revenue_items ri ON r.revenue_id = ri.revenue_id
                LEFT JOIN revenue_types rt ON ri.revenue_type_id = rt.revenue_type_id
                WHERE r.store_id = %s
                    AND r.revenue_date BETWEEN %s AND %s
                GROUP BY r.revenue_id
            ) as revenue_totals
        """
        params = (store_id, start_date, end_date)
        result = cls._execute_query(query, params, fetch_one=True)
        return result['total_net'] if result else 0