"""Reader for MLB The Show 26 (Switch) franchise saves.

    from mlb26save import open_save
    save = open_save(r"E:\\MLB 26 FINAL\\profile\\save\\<profile-id>")
    league = save.export()          # plain dict, ready for JSON
"""
from .container import SaveSlot, open_save
from .database import Database

__all__ = ["SaveSlot", "open_save", "Database"]
__version__ = "0.1.0"
