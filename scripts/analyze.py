#!/usr/bin/env python3
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Set
import ast
from collections import defaultdict

class RepositoryAnalyzer:
    def __init__(self):
        self.root_dir = Path('.')
        
    def find_duplicates(self) -> Dict[str, List[str]]:
        """Find duplicate files by content."""
        hash_map = defaultdict(list)
        
        for file_path in self.root_dir.rglob('*'):
            if file_path.is_file() and not self._is_ignored(file_path):
                file_hash = self._get_file_hash(file_path)
                hash_map[file_hash].append(str(file_path))
                
        return {h: files for h, files in hash_map.items() if len(files) > 1}
    
    def find_unused_imports(self) -> Dict[str, List[str]]:
        """Find unused imports in Python files."""
        unused_imports = {}
        
        for py_file in self.root_dir.rglob('*.py'):
            if not self._is_ignored(py_file):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                    
                    imports = set()
                    used = set()
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            for name in node.names:
                                imports.add(name.name)
                        elif isinstance(node, ast.Name):
                            used.add(node.id)
                    
                    unused = imports - used
                    if unused:
                        unused_imports[str(py_file)] = list(unused)
                except Exception as e:
                    print(f"Error analyzing {py_file}: {e}")
                    
        return unused_imports

    def find_dead_code(self) -> Dict[str, List[str]]:
        """Find potentially unused functions and classes."""
        dead_code = {}
        
        for py_file in self.root_dir.rglob('*.py'):
            if not self._is_ignored(py_file):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                    
                    defined = set()
                    used = set()
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                            defined.add(node.name)
                        elif isinstance(node, ast.Name):
                            if isinstance(node.ctx, ast.Load):
                                used.add(node.id)
                    
                    unused = defined - used
                    if unused:
                        dead_code[str(py_file)] = list(unused)
                except Exception as e:
                    print(f"Error analyzing {py_file}: {e}")
                    
        return dead_code

    def _get_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
                
        return sha256_hash.hexdigest()
    
    def _is_ignored(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        ignored = {'.git', '__pycache__', 'venv', 'env', '.env', 'node_modules'}
        return any(part in ignored for part in path.parts)
    
    def analyze(self):
        """Run all analysis and print results."""
        print("\n=== Repository Analysis ===\n")
        
        # Find duplicates
        duplicates = self.find_duplicates()
        if duplicates:
            print("Duplicate files found:")
            for hash_val, files in duplicates.items():
                print(f"\nDuplicate set:")
                for f in files:
                    print(f"  - {f}")
        else:
            print("No duplicate files found.")
            
        # Find unused imports
        unused_imports = self.find_unused_imports()
        if unused_imports:
            print("\nUnused imports found:")
            for file, imports in unused_imports.items():
                print(f"\n{file}:")
                for imp in imports:
                    print(f"  - {imp}")
        else:
            print("\nNo unused imports found.")
            
        # Find dead code
        dead_code = self.find_dead_code()
        if dead_code:
            print("\nPotentially unused code found:")
            for file, unused in dead_code.items():
                print(f"\n{file}:")
                for item in unused:
                    print(f"  - {item}")
        else:
            print("\nNo potentially unused code found.")

if __name__ == '__main__':
    analyzer = RepositoryAnalyzer()
    analyzer.analyze()
