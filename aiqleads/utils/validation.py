import os
from pathlib import Path
from typing import List, Set

class PathValidator:
    def __init__(self, base_dir: str = "aiqleads"):
        self.base_dir = Path(base_dir)
        self.allowed_directories = {
            'backend',
            'ai_models',
            'scraping',
            'services',
            'deployment',
            'tests',
            'docs'
        }

    def validate_path(self, path: str) -> bool:
        """Validate if a path follows project structure rules"""
        try:
            path = Path(path)
            parts = path.parts
            if not parts:
                return False
            root_dir = parts[0] if parts[0] != self.base_dir.name else (
                parts[1] if len(parts) > 1 else None
            )
            if not root_dir or root_dir not in self.allowed_directories:
                return False
            return True
        except Exception:
            return False

    def suggest_path(self, filename: str, component_type: str) -> str:
        """Suggest correct path for a file based on type"""
        type_to_dir = {
            'api': 'backend',
            'model': 'ai_models',
            'scraper': 'scraping',
            'service': 'services',
            'test': 'tests',
            'doc': 'docs'
        }
        
        target_dir = type_to_dir.get(component_type, 'backend')
        return str(Path(self.base_dir) / target_dir / filename)

    def list_invalid_paths(self, directory: str = None) -> List[str]:
        """Find all invalid paths in project"""
        invalid_paths = []
        scan_dir = self.base_dir if not directory else Path(directory)
        
        for root, _, files in os.walk(scan_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(self.base_dir)
                if not self.validate_path(str(rel_path)):
                    invalid_paths.append(str(rel_path))
                    
        return invalid_paths