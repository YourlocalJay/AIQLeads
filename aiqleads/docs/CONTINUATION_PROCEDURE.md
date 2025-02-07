# AIQLeads Continuation Procedure

## Session Start

1. Status Check
   ```python
   # Get current status
   status = tracker.get_status_summary()
   print("Current Status:", status)
   ```

2. File Review Order
   - Check documentation updates
   - Review component status
   - Validate file locations
   - Verify dependencies

3. Environment Setup
   ```bash
   # Environment variables
   cp .env.example .env
   # Update with necessary credentials
   ```

## During Development

1. File Location Validation
   ```python
   validator = PathValidator()
   is_valid = validator.validate_path("backend/api/v1/leads.py")
   ```

2. Status Updates
   ```python
   tracker.update_status(
       component_id="backend/api/v1/leads.py",
       status="🟡 In Progress"
   )
   ```

3. Documentation Updates
   - Keep UNIVERSAL_PROMPT.md current
   - Update component status
   - Add implementation notes

## Session End

1. Status Documentation
   ```python
   # Get final status
   final_status = tracker.get_status_summary()
   print("Session End Status:", final_status)
   ```

2. Next Steps
   - Document completed work
   - List pending tasks
   - Note any blockers
   - Update priorities

3. Cleanup
   - Commit documentation
   - Update tracking files
   - Validate file locations

4. End of Session Command
   When typing "End chat", "End of chat", or "End session":
   - All above steps are executed
   - Status is saved
   - Next session brief is generated