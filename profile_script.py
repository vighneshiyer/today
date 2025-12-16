#!/usr/bin/env python3
import cProfile
import pstats
import sys
from io import StringIO

from today.scripts.today import run

# Profile the script
profiler = cProfile.Profile()
profiler.enable()

run(["--dir", "./example"])

profiler.disable()

# Print stats
s = StringIO()
ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
ps.print_stats(50)  # Top 50 functions
print(s.getvalue())

# Also print by tottime
s2 = StringIO()
ps2 = pstats.Stats(profiler, stream=s2).sort_stats('tottime')
ps2.print_stats(50)
print("\n\n===== SORTED BY TOTTIME =====\n\n")
print(s2.getvalue())
