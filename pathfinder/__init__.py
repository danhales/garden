# pathfinder/__init__.py - Add this content
from pathlib import Path as PathLib
from .core.models import PathRoute  # Renamed to avoid collision
from .core.managers import ContextManager
from .ui.themes import ThemeManager

# Create our main class
class Pathfinder:
    def __init__(self, neo4j_uri=None, username=None, password=None, database=None):
        self.uri = neo4j_uri or 'bolt://localhost:7687'
        self.username = username or 'neo4j'
        self.password = password or 'neo4j'
        self.database = database or 'neo4j'
        
        # Setup storage
        storage_dir = PathLib.home() / '.pathfinder'
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.context_manager = ContextManager(storage_dir=storage_dir)
        self.theme_manager = ThemeManager(themes_dir=storage_dir / 'themes')
        self.module_path = None