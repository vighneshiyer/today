#!/usr/bin/env python3
"""Profile the fast mode."""
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

t_start = time.perf_counter()

# Time individual imports
t1 = time.perf_counter()
import argparse
t2 = time.perf_counter()
from datetime import date
t3 = time.perf_counter()
from pathlib import Path
t4 = time.perf_counter()

from today.cli import build_parser, parse_args, parse_task_files
t5 = time.perf_counter()
from today.simple_output import simple_display
t6 = time.perf_counter()

# Run the script
parser = build_parser()
t7 = time.perf_counter()
cli_args = parse_args(parser, ["--fast", "--dir", "./example"])
t8 = time.perf_counter()
tasks = parse_task_files(cli_args)
t9 = time.perf_counter()
simple_display(cli_args, tasks)
t10 = time.perf_counter()

print("\n\n=== FAST MODE TIMING ===")
print(f"Import argparse: {(t2-t1)*1000:.2f}ms")
print(f"Import datetime: {(t3-t2)*1000:.2f}ms")
print(f"Import pathlib: {(t4-t3)*1000:.2f}ms")
print(f"Import today.cli: {(t5-t4)*1000:.2f}ms")
print(f"Import simple_output: {(t6-t5)*1000:.2f}ms")
print(f"build_parser: {(t7-t6)*1000:.2f}ms")
print(f"parse_args: {(t8-t7)*1000:.2f}ms")
print(f"parse_task_files: {(t9-t8)*1000:.2f}ms")
print(f"simple_display: {(t10-t9)*1000:.2f}ms")
print(f"\nTotal: {(t10-t_start)*1000:.2f}ms")
