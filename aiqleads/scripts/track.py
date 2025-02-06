#!/usr/bin/env python3
"""CLI utility for project tracking"""

import sys
import json
from pathlib import Path
import argparse

# Add project root to path
root_dir = str(Path(__file__).resolve().parents[2])
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from aiqleads.core.project_tracking import ProjectTracker, ComponentStatus

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Project tracking utility")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Get component status")
    status_parser.add_argument("component_id", help="Component ID")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update component status")
    update_parser.add_argument("component_id", help="Component ID")
    update_parser.add_argument("status", choices=[
        ComponentStatus.NOT_STARTED,
        ComponentStatus.IN_PROGRESS,
        ComponentStatus.REVIEW,
        ComponentStatus.TESTING,
        ComponentStatus.COMPLETED,
        ComponentStatus.BLOCKED
    ], help="New status")
    update_parser.add_argument("--notes", help="Status update notes")
    
    # Report command
    subparsers.add_parser("report", help="Generate status report")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    tracker = ProjectTracker()
    
    if args.command == "status":
        report = tracker.generate_report()
        if args.component_id in report["components"]:
            print(json.dumps(report["components"][args.component_id], indent=2))
        else:
            print(f"Component not found: {args.component_id}")
            sys.exit(1)
    
    elif args.command == "update":
        if not tracker.update_status(args.component_id, args.status, args.notes):
            print(f"Failed to update {args.component_id}")
            sys.exit(1)
        print(f"Updated {args.component_id} to {args.status}")
    
    elif args.command == "report":
        report = tracker.generate_report()
        print(json.dumps(report, indent=2))
    
    else:
        print("No command specified")
        sys.exit(1)

if __name__ == "__main__":
    main()