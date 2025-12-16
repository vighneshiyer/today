#!/usr/bin/env python3
import pstats

# Print stats sorted by cumulative time
ps = pstats.Stats('profile.stats')
print("===== SORTED BY CUMULATIVE TIME =====\n")
ps.sort_stats('cumulative').print_stats(50)

print("\n\n===== SORTED BY TOTAL TIME =====\n")
ps.sort_stats('tottime').print_stats(50)

print("\n\n===== CALLERS OF EXPENSIVE FUNCTIONS =====\n")
ps.print_callers(30)
