"""Validation utilities for project structure and components"""

def validate_path(path: str, reference_structure: str) -> bool:
    """
    Validate that a component path exists in the reference structure.
    
    Args:
        path: Component path to validate
        reference_structure: Project structure reference content
    
    Returns:
        bool: True if path is valid, False otherwise
    """
    # Clean path for comparison
    clean_path = path.replace('aiqleads/', '')
    
    # Check each line in reference structure
    for line in reference_structure.split('\n'):
        if '#' in line:  # Line contains a file with description
            file_path = line.split('#')[0].strip().strip('├──').strip('└──').strip()
            if clean_path == file_path:
                return True
    
    return False