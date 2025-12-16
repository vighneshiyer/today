"""Simple text output for fast display without rich."""
from datetime import date, timedelta
from typing import List

from today.task import Task
from today.cli import CliArgs


def simple_display(args: CliArgs, tasks: List[Task]) -> None:
    """Display tasks using simple text output (no rich dependency)."""
    print()
    title = f"Tasks for today ({args.today})"
    if args.lookahead_days != timedelta(0):
        title += f" (+{args.lookahead_days.days} days)"
    print(title)
    print()
    
    # Separate priority and regular tasks
    priority_tasks = [t for t in tasks if t.attrs.priority_attr is not None]
    other_tasks = [t for t in tasks if t.attrs.priority_attr is None]
    
    if priority_tasks:
        print("Priority Tasks:")
        for i, task in enumerate(priority_tasks):
            path = " / ".join(task.path) if task.path else ""
            summary = task.summary(args.today)
            file_ref = f"{task.file_path.relative_to(args.task_dir)}:{task.line_number}"
            print(f"  {i} - {path} → {task.title} {summary} ({file_ref})")
        print()
    
    if other_tasks:
        # Group by file and heading
        current_file = None
        current_path = []
        
        for i, task in enumerate(other_tasks):
            task_idx = i + len(priority_tasks)
            
            # Print file header if changed
            if task.file_path != current_file:
                current_file = task.file_path
                current_path = []
                print(f"{task.file_path.relative_to(args.task_dir)}:")
            
            # Print heading hierarchy
            for depth, heading in enumerate(task.path):
                if depth >= len(current_path) or current_path[depth] != heading:
                    # Update and print new path
                    current_path = task.path[:depth+1]
                    print("  " * depth + f"{heading}:")
            
            # Print the task
            summary = task.summary(args.today)
            indent = "  " * len(task.path)
            print(f"{indent}  {task_idx} - {task.title} {summary} (:{task.line_number})")
            
            # Print subtasks
            for subtask in task.subtasks:
                if not subtask.done and subtask.is_displayed(args.today, args.lookahead_days.days):
                    subtask_summary = subtask.summary(args.today)
                    print(f"{indent}    • {subtask.title} {subtask_summary}")
    
    print()
