from pathlib import Path
import json
from typing import Dict, Optional, Any
from enum import Enum
import logging
from datetime import datetime

class ComponentStatus(str, Enum):
    NOT_STARTED = "🔴 Not Started"
    IN_PROGRESS = "🟡 In Progress"
    IN_REVIEW = "🟣 In Review"
    TESTING = "🔵 Testing"
    COMPLETED = "🟢 Completed"
    BLOCKED = "⭕ Blocked"

class ProjectTracker:
    def __init__(self, base_dir: str = "aiqleads"):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.status_file = self.data_dir / "project_status.json"
        self.registry_file = self.data_dir / "component_registry.json"
        self.history_file = self.data_dir / "status_history.json"
        
        self._load_data()
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.data_dir / "project_tracking.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("ProjectTracker")

    def _load_data(self):
        """Load tracking data from storage files"""
        self.components = self._load_json(self.registry_file, {})
        self.status = self._load_json(self.status_file, {})
        self.history = self._load_json(self.history_file, [])