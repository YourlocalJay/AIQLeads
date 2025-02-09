# Chat End Sequence Protocol

## 1. Trigger Conditions
- User types "End of chat." or equivalent
- System state allows for clean termination
- No pending critical operations

## 2. Pre-End Validation
```python
def validate_end_conditions():
    # Check system state
    if has_pending_operations():
        raise StateError("Cannot end chat with pending operations")
        
    # Verify data consistency
    if not is_data_consistent():
        raise DataError("Data inconsistency detected")
        
    # Check resource cleanup
    if has_unclosed_resources():
        raise ResourceError("Unclosed resources detected")

    return True
```

## 3. State Collection
```python
def collect_state():
    return {
        "repository": {
            "url": current_repo_url,
            "branch": current_branch,
            "owner": repo_owner,
            "access": access_type
        },
        "status": {
            "completed": list_completed_tasks(),
            "pending": list_pending_tasks(),
            "current": get_current_state()
        },
        "context": {
            "files": list_relevant_files(),
            "critical_rules": get_critical_rules(),
            "requirements": get_requirements()
        }
    }
```

## 4. Generate Continuation Data
```python
def generate_continuation():
    state = collect_state()
    return f"""# Prompt for Next Chat
Please continue with repository: {state['repository']['url']}
- Branch: {state['repository']['branch']}
- Owner: {state['repository']['owner']} 
- Access: {state['repository']['access']}

Current Status:
{format_status(state['status'])}

Next Tasks:
{format_tasks(state['status']['pending'])}

Critical Requirements:
{format_rules(state['context']['critical_rules'])}

Files of Interest:
{format_files(state['context']['files'])}

End of Chat."""
```

## 5. Exit Sequence
```python
def execute_end_sequence():
    try:
        # Validate end conditions
        validate_end_conditions()
        
        # Collect final state
        state = collect_state()
        
        # Generate continuation data
        continuation = generate_continuation()
        
        # Cleanup resources
        cleanup_resources()
        
        # Output continuation prompt
        print(continuation)
        
        # Final state verification
        verify_clean_state()
        
    except Exception as e:
        handle_end_sequence_error(e)
```

## 6. Verification Checklist
- [ ] All system resources properly closed
- [ ] State data collected and verified
- [ ] Continuation data generated
- [ ] Critical rules preserved
- [ ] No data loss occurred
- [ ] Clean exit state achieved

## 7. Sequence Rules
1. Never skip validation steps
2. Always generate continuation data
3. Include all critical rules
4. List all relevant files
5. Document current status
6. Specify next tasks
7. End with "End of Chat."

## 8. Error Recovery
```python
def handle_end_sequence_error(error):
    # Log error
    log_error(error)
    
    # Attempt cleanup
    emergency_cleanup()
    
    # Generate safe continuation
    safe_continuation = generate_safe_continuation()
    
    # Report error state
    report_error_state()
```

## 9. Implementation Notes
- Validate before executing end sequence
- Never skip steps in the process
- Always include continuation data
- Follow exact format for continuation prompt
- Maintain consistent structure
- Include all repository details
- End with explicit termination phrase