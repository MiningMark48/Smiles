from typing import Any
from sqlalchemy import Table

from util.data.value_helper import ValueHelper


class TableHelper:
    """
    Helper class for handling SQLAlchemy tables
    """

    def __init__(self, table: Table, conn):
        """
        Initialize the helper class

        Args:
            table (Table): The SQLAlchemy table to use
            conn (sqlalchemy.Connection): The engine connection
        """

        self.table = table
        self.conn = conn

    def delete(self, name: str) -> bool:
        """
        Deletes a specific data from the table

        Args:
            name (str): The name of the data to delete

        Returns:
            bool: Returns true if the data was deleted successfully
        """

        val = self.fetch_by_name(name)
        if val is not None:
            rep = self.table.delete().where(self.table.columns.name == name)
            self.conn.execute(rep)
            return True
        else:
            return False

    def delete_all(self):
        """
        Deletes all data from the table
        """

        rep = self.table.delete()
        self.conn.execute(rep)

    def fetch_all(self) -> list:
        """
        Fetch all data from the table

        Returns:
            list: List of all data in the table
        """

        sel = self.table.select()
        return list(self.conn.execute(sel))

    def fetch_all_by_name(self, name: str) -> list:
        """
        Fetch all data by name

        Args:
            name (str): The name to fetch

        Returns:
            list: List of data
        """

        sel = self.table.select().where(self.table.columns.name == name)
        return list(self.conn.execute(sel))

    def fetch_by_name(self, name: str, val_pos=2) -> Any:
        """
        Fetch a specific data entry from the table by position

        Args:
            name (str): The name to fetch
            val_pos (int, optional): Position of the value. Defaults to 2.

        Returns:
            any: The value at the given position
        """

        return ValueHelper.list_tuple_value(self.fetch_all_by_name(name), val_pos)

    def insert_(self, items: list):
        """
        Insert a list of items into the table
        """

        self.conn.execute(self.table.insert(), items)

    def set(self, name: str, value) -> Any:
        """
        Set a data entry value in the table by name
        (Overwrites existing entry)

        Args:
            name (str): Name of the entry
            value (any): Value to set

        Returns:
            any: The given value
        """

        val = self.fetch_by_name(name)
        if val is not None:
            rep = self.table.update().where(self.table.columns.name == name).values(value=value)
            self.conn.execute(rep)
            return value
        else:
            self.insert_([{'name': name, 'value': value}])
            return value

    def toggle_boolean(self, name: str, default_val=True) -> bool:
        """
        Toggles a boolean value date entry in the table by name

        Returns:
            bool: Returns the new value of the entry
        """

        val = self.fetch_by_name(name)
        if val is not None:
            new_val = not val
            rep = self.table.update().where(self.table.columns.name == name).values(value=new_val)
            self.conn.execute(rep)
            return new_val
        else:
            self.insert_([{'name': name, 'value': default_val}])
            return True
