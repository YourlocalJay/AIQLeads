#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
import ast
from collections import defaultdict


class RepoAnalyzer:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.file_hashes: Dict[str, List[str]] = defaultdict(list)
        self.unused_imports: Dict[str, List[str]] = {}
        self.dead_code: Dict[str, List[str]] = {}
        self.circular_deps: List[Tuple[str, str]] = []

    def compute_file_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash of file content."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def find_duplicate_files(self) -> Dict[str, List[str]]:
        """Find files with identical content."""
        for filepath in self.repo_path.rglob("*"):
            if filepath.is_file() and not any(
                p.startswith(".") for p in filepath.parts
            ):
                file_hash = self.compute_file_hash(filepath)
                self.file_hashes[file_hash].append(str(filepath))

        return {h: paths for h, paths in self.file_hashes.items() if len(paths) > 1}

    def analyze_imports(self, filepath: Path) -> List[str]:
        """Analyze Python file for unused imports."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            imports = set()
            used_names = set()

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for name in node.names:
                        imports.add(name.name)
                elif isinstance(node, ast.Name):
                    used_names.add(node.id)

            return list(imports - used_names)
        except Exception:
            return []

    def find_unused_imports(self) -> Dict[str, List[str]]:
        """Find unused imports in Python files."""
        for filepath in self.repo_path.rglob("*.py"):
            if not any(p.startswith(".") for p in filepath.parts):
                unused = self.analyze_imports(filepath)
                if unused:
                    self.unused_imports[str(filepath)] = unused
        return self.unused_imports

    def find_dead_code(self) -> Dict[str, List[str]]:
        """Find potentially dead code using static analysis."""
        for filepath in self.repo_path.rglob("*.py"):
            if not any(p.startswith(".") for p in filepath.parts):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())

                    unused_funcs = []
                    defined_funcs = set()
                    called_funcs = set()

                    # Find defined functions
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            defined_funcs.add(node.name)
                        elif isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Name):
                                called_funcs.add(node.func.id)

                    # Find unused functions
                    unused_funcs = defined_funcs - called_funcs
                    if unused_funcs:
                        self.dead_code[str(filepath)] = list(unused_funcs)

                except Exception:
                    continue

        return self.dead_code

    def detect_circular_imports(self) -> List[Tuple[str, str]]:
        """Detect potential circular imports."""
        import_graph = defaultdict(set)

        # Build import graph
        for filepath in self.repo_path.rglob("*.py"):
            if not any(p.startswith(".") for p in filepath.parts):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())

                    module_name = (
                        str(filepath.relative_to(self.repo_path))
                        .replace("/", ".")
                        .replace(".py", "")
                    )

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            if isinstance(node, ast.ImportFrom) and node.module:
                                import_graph[module_name].add(node.module)
                            for name in node.names:
                                import_graph[module_name].add(name.name.split(".")[0])

                except Exception:
                    continue

        # Detect cycles
        def has_cycle(node: str, visited: Set[str], path: Set[str]) -> bool:
            if node in path:
                self.circular_deps.append((node, list(path)[-1]))
                return True
            if node in visited:
                return False

            visited.add(node)
            path.add(node)

            for neighbor in import_graph[node]:
                if has_cycle(neighbor, visited, path):
                    return True

            path.remove(node)
            return False

        visited = set()
        for node in import_graph:
            if node not in visited:
                has_cycle(node, visited, set())

        return self.circular_deps

    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report."""
        return {
            "duplicate_files": self.find_duplicate_files(),
            "unused_imports": self.find_unused_imports(),
            "dead_code": self.find_dead_code(),
            "circular_dependencies": self.detect_circular_imports(),
        }

    def save_report(self, report: Dict, output_file: str = "repo_analysis.json"):
        """Save analysis report to file."""
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)


if __name__ == "__main__":
    analyzer = RepoAnalyzer(".")
    report = analyzer.generate_report()
    analyzer.save_report(report)

    # Print summary
    print("\n=== Repository Analysis Summary ===")
    print(
        f"Duplicate Files: {sum(len(files) for files in report['duplicate_files'].values())}"
    )
    print(f"Files with Unused Imports: {len(report['unused_imports'])}")
    print(f"Files with Dead Code: {len(report['dead_code'])}")
    print(f"Circular Dependencies: {len(report['circular_dependencies'])}")
