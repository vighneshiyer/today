"""Lightweight argument parsing for fast mode."""
from pathlib import Path
from datetime import date, timedelta
from typing import List, Optional, Union
from dataclasses import dataclass


@dataclass
class FastCliArgs:
    """Lightweight version of CliArgs for fast mode."""
    task_dir: Path
    today: date
    lookahead_days: timedelta
    task_id: Optional[Union[int, str]]
    fast: bool = True

    def task_date_filter(self) -> date:
        return self.today + self.lookahead_days


def parse_fast_args(args: List[str]) -> FastCliArgs:
    """
    Fast argument parser that avoids argparse overhead.
    Only handles the common case: --fast --dir <path> [--days N] [--today DATE] [task_id]
    """
    task_dir = Path.cwd().resolve()
    lookahead_days = timedelta(days=0)
    today = date.today()
    task_id: Optional[Union[int, str]] = None
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg == "--dir" and i + 1 < len(args):
            task_dir = Path(args[i + 1]).resolve()
            i += 2
        elif arg == "--days" and i + 1 < len(args):
            lookahead_days = timedelta(days=int(args[i + 1]))
            i += 2
        elif arg == "--today" and i + 1 < len(args):
            today_split = args[i + 1].split("/")
            today = date(int(today_split[2]), int(today_split[0]), int(today_split[1]))
            i += 2
        elif arg == "--fast":
            i += 1
        elif arg in ("-h", "--help"):
            print("Usage: today [--fast] [--dir DIR] [--days DAYS] [--today DATE] [task_id]")
            import sys
            sys.exit(0)
        elif not arg.startswith("-"):
            # This is the task_id
            try:
                task_id = int(arg)
            except ValueError:
                task_id = arg
            i += 1
        else:
            # Unknown argument, skip it
            i += 1
    
    if not task_dir.is_dir():
        raise ValueError(f"Provided --dir {task_dir} is not a directory")
    
    return FastCliArgs(
        task_dir=task_dir,
        today=today,
        lookahead_days=lookahead_days,
        task_id=task_id,
        fast=True,
    )
