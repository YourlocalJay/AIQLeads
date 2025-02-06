"""Status storage and retrieval functionality for project tracking"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from .logging import setup_logger

logger = setup_logger(__name__)

class StatusStore:
    """Manages persistent storage of project status information."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir.mkdir(exist_ok=True)
        self.status_file = self.data_dir / 'project_status.json'
        self.registry_file = self.data_dir / 'component_registry.json'
        self.load_data()
    
    def load_data(self):
        """Load status and registry data."""
        if self.status_file.exists():
            with open(self.status_file) as f:
                self.status_data = json.load(f)
        else:
            self.status_data = {
                "components": {},
                "metrics": {
                    "completion_percentage": 0,
                    "total_components": 0,
                    "completed_components": 0,
                    "last_updated": datetime.now().isoformat()
                }
            }
            
        if self.registry_file.exists():
            with open(self.registry_file) as f:
                self.registry = json.load(f)
        else:
            self.registry = {
                "api": {},
                "core": {},
                "models": {},
                "services": {},
                "utils": {},
                "scrapers": {},
                "parsers": {}
            }
        
        self.save_data()
    
    def save_data(self):
        """Save current status and registry data."""
        with open(self.status_file, 'w') as f:
            json.dump(self.status_data, f, indent=2)
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def find_duplicate(self, component_type: str, component_hash: str) -> Optional[str]:
        """Find component with matching functionality hash."""
        for comp_id, comp_data in self.registry[component_type].items():
            if comp_data.get('hash') == component_hash:
                return comp_id
        return None
    
    def register_component(self, component_type: str, component_id: str, 
                         component_def: Dict) -> bool:
        """Register new component in registry."""
        if component_type not in self.registry:
            logger.error(f"Invalid component type: {component_type}")
            return False
            
        self.registry[component_type][component_id] = {
            "hash": component_def.get('hash'),
            "registered_at": datetime.now().isoformat(),
            "definition": component_def
        }
        
        self.status_data["components"][component_id] = {
            "status": "🔴 Not Started",
            "history": [],
            "dependencies": []
        }
        
        self.update_metrics()
        self.save_data()
        return True
    
    def update_status(self, component_id: str, status: str, 
                     notes: Optional[str] = None) -> bool:
        """Update component status and history."""
        if component_id not in self.status_data["components"]:
            logger.error(f"Component not registered: {component_id}")
            return False
            
        component = self.status_data["components"][component_id]
        previous_status = component["status"]
        component["status"] = status
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "from_status": previous_status,
            "to_status": status
        }
        if notes:
            history_entry["notes"] = notes
            
        component["history"].append(history_entry)
        
        self.update_metrics()
        self.save_data()
        return True
    
    def update_metrics(self):
        """Update project completion metrics."""
        total = len(self.status_data["components"])
        completed = sum(
            1 for c in self.status_data["components"].values()
            if c["status"] == "🟢 Completed"
        )
        
        self.status_data["metrics"] = {
            "completion_percentage": (completed / total * 100) if total > 0 else 0,
            "total_components": total,
            "completed_components": completed,
            "last_updated": datetime.now().isoformat()
        }
    
    def generate_report(self) -> Dict:
        """Generate comprehensive status report."""
        return {
            "metrics": self.status_data["metrics"],
            "components": {
                comp_id: {
                    "status": comp_data["status"],
                    "history": comp_data["history"][-5:],  # Last 5 updates
                    "dependencies": comp_data["dependencies"]
                }
                for comp_id, comp_data in self.status_data["components"].items()
            },
            "generated_at": datetime.now().isoformat()
        }