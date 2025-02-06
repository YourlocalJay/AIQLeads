#!/usr/bin/env python3
"""Script runner that handles Python path setup"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python run.py <script_name> [args...]")
        print("\nAvailable scripts:")
        print("  register_components - Register project components")
        print("  track status <component_id> - Get component status")
        print("  track update <component_id> <status> - Update component status")
        print("  track report - Generate status report")
        sys.exit(1)

    script_name = sys.argv[1]
    script_args = sys.argv[2:]

    if script_name == "register_components":
        from aiqleads.scripts.register_components import register_core_components
        register_core_components()
    elif script_name == "track":
        from aiqleads.scripts.track import main
        sys.argv = [sys.argv[0]] + script_args
        main()
    else:
        print(f"Unknown script: {script_name}")
        sys.exit(1)

if __name__ == "__main__":
    main()