# models/setting.py
from models.base_model import BaseModel

class Setting(BaseModel):
    """
    Model for application settings stored in the database.
    This model interacts with the 'settings' table.
    The table is expected to have 'setting_key' (as primary key) and 'setting_value'.
    """
    _table_name = 'settings'
    _primary_key = 'setting_key' # Use setting_key as the primary key

    def __init__(self, setting_key=None, setting_value=None, updated_at=None):
        """
        Initializes a Setting object.
        """
        # We don't call super().__init__ here because the structure is simpler
        # and doesn't have the standard columns like created_by, etc.
        self.setting_key = setting_key
        self.setting_value = setting_value
        self.updated_at = updated_at
        self._last_error = None

    def save(self, user_id=None): # user_id is unused here but kept for compatibility
        """
        Saves or updates a setting in the database using an "upsert" operation.
        If the setting_key exists, it updates the value. If not, it inserts a new row.
        """
        if not self.setting_key:
            raise ValueError("Setting key cannot be empty.")

        query = """
            INSERT INTO settings (setting_key, setting_value)
            VALUES (%s, %s)
            ON CONFLICT (setting_key) DO UPDATE SET
                setting_value = EXCLUDED.setting_value,
                updated_at = NOW()
            RETURNING *;
        """
        params = (self.setting_key, self.setting_value)
        
        result = self._execute_query(query, params, fetch_one=True, commit=True)

        if isinstance(result, str) and result.startswith("duplicate_key_error:"):
            self._last_error = result
            return False
        elif result:
            for key, value in result.items():
                setattr(self, key, value)
            self._last_error = None
            return True
        
        self._last_error = "Unknown error during save."
        return False

    @classmethod
    def get_value(cls, key, default=None):
        """
        A convenience method to get a setting's value directly.
        """
        setting = cls.find_by_id(key)
        return setting.setting_value if setting else default