#!/usr/bin/env python3
"""Profile the today script to find performance bottlenecks."""
import time
import sys
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).parent))

# Time imports
t_start = time.perf_counter()
from rich.console import Console
t_rich = time.perf_counter()
print(f"Import rich: {(t_rich - t_start) * 1000:.2f}ms")

from today.cli import (
    build_parser,
    parse_args,
    parse_task_files,
    display_specific_task,
    tasks_to_tree,
)
t_cli = time.perf_counter()
print(f"Import today.cli: {(t_cli - t_rich) * 1000:.2f}ms")

# Now time the actual execution
t1 = time.perf_counter()
parser = build_parser()
t2 = time.perf_counter()
cli_args = parse_args(parser, ["--dir", "./example"])
t3 = time.perf_counter()
console = Console()
t4 = time.perf_counter()
tasks = parse_task_files(cli_args)
t5 = time.perf_counter()
tree = tasks_to_tree(cli_args, tasks)
t6 = time.perf_counter()
console.print("")
console.print(tree)
console.print("")
t7 = time.perf_counter()

print("\n=== TIMING BREAKDOWN ===")
print(f"Total imports: {(t_cli - t_start) * 1000:.2f}ms")
print(f"  - rich: {(t_rich - t_start) * 1000:.2f}ms")
print(f"  - today.cli: {(t_cli - t_rich) * 1000:.2f}ms")
print(f"\nExecution:")
print(f"  build_parser: {(t2 - t1) * 1000:.2f}ms")
print(f"  parse_args: {(t3 - t2) * 1000:.2f}ms")
print(f"  create Console: {(t4 - t3) * 1000:.2f}ms")
print(f"  parse_task_files: {(t5 - t4) * 1000:.2f}ms")
print(f"  tasks_to_tree: {(t6 - t5) * 1000:.2f}ms")
print(f"  print tree: {(t7 - t6) * 1000:.2f}ms")
print(f"\nTotal execution: {(t7 - t1) * 1000:.2f}ms")
print(f"TOTAL (imports + execution): {(t7 - t_start) * 1000:.2f}ms")
