#!/usr/bin/env python3
import subprocess
import datetime
import sys

def run_command(command):
    try:
        process = subprocess.run(command, shell=True, check=True, 
                               capture_output=True, text=True)
        print(process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def sync_changes():
    print("\n🔄 Syncing changes...")
    
    # Pull latest changes
    if not run_command("git pull origin main"):
        print("❌ Failed to pull changes")
        return False
        
    # Add all changes
    if not run_command("git add ."):
        print("❌ Failed to stage changes")
        return False
    
    # Create commit message with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"Auto-sync: {timestamp}"
    
    # Commit changes
    if not run_command(f'git commit -m "{commit_msg}"'):
        print("ℹ️ No changes to commit")
        return True
    
    # Push changes
    if not run_command("git push origin main"):
        print("❌ Failed to push changes")
        return False
    
    print("✅ Sync completed successfully!")
    return True

if __name__ == "__main__":
    sys.exit(0 if sync_changes() else 1)
