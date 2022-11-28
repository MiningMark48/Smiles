import os
import logging

log = logging.getLogger("smiles")


def delete_database_guild(guild_id: str):
    """Delete a guild's database file from the data directory.

    Args:
        guild_id (str): The ID of the guild whose database file is to be deleted.
    """
    
    folder_name = "data"
    prefix = "guild_"
    path = f"{folder_name}/{prefix}{guild_id}.db"
    if os.path.exists(path):
        os.remove(path)
        log.debug(f"Deleted {path}")
