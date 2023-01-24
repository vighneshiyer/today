import argparse
import sys
from pathlib import Path
import itertools
from datetime import date, timedelta
from typing import List
import functools

from rich.tree import Tree
from rich.console import Console
from rich.markdown import Markdown

from today.task import Task
from today.parser import parse_markdown
from today.output import task_should_be_displayed, task_summary, days, task_details, task_sorter


def run(args) -> None:
    # Fetch Markdown task files
    if args.dir:
        assert Path(args.dir).is_dir()
        root = Path(args.dir)
    else:
        root = Path.cwd()
    md_files = list(root.resolve().glob("*.md"))

    # Use the mocked 'today' date if requested, else use the actual date
    if args.today:
        mock_today_split = args.today.split('/')
        today = date(int(mock_today_split[2]), int(mock_today_split[0]), int(mock_today_split[1]))
    else:
        today = date.today()

    # Parse each Markdown task file
    tasks_by_file: List[List[Task]] = [parse_markdown(file.read_text().split('\n'), today=today) for file in md_files]

    # Set each task's file path
    for filepath, tasklist in zip(md_files, tasks_by_file):
        for task in tasklist:
            task.file_path = filepath

    # Flatten the task list
    tasks: List[Task] = list(itertools.chain(*tasks_by_file))

    # Only look at tasks that have a due/reminder date on today or number of 'days' in the future
    task_date_limit = today + timedelta(days=args.days)
    tasks_visible: List[Task] = [task for task in tasks if task_should_be_displayed(task, task_date_limit)]

    # Sort tasks by their headings and due dates
    tasks_visible.sort(key=functools.partial(task_sorter, today=today))

    console = Console()

    # If a specific task id is given, print its description and details and exit
    if args.task_id is not None:
        if args.task_id < 0 or args.task_id >= len(tasks_visible):
            console.print(f"The task_id {args.task_id} does not exist")
            sys.exit(1)
        task = tasks_visible[args.task_id]
        details = task_details(task, args.task_id, today)
        console.print("")
        console.print(Markdown(details))
        console.print("")

        if len(task.subtasks) > 0:
            console.print(Markdown(f"**Subtasks**:"))
            console.print("")
        for subtask in task.subtasks:
            subtask_summary = task_summary(subtask, today)
            console.print(Markdown(f"{subtask.title} {subtask_summary}"))
        if len(task.subtasks) > 0:
            console.print("")

        sys.exit(0)

    # Print tasks as a tree
    tree = Tree(f"[bold underline]Tasks for today ({today})[/bold underline]" +
                ("" if args.days == 0 else f" (+{days(timedelta(days=args.days))})"))

    def add_to_tree(task: Task, tree: Tree, task_idx: int) -> Tree:
        if len(task.path) == 0:  # Base case
            parent = tree.add(Markdown(f"**{task_idx}** - {task.title} {task_summary(task, today)}"))
            if task.subtasks:
                for subtask in task.subtasks:
                    parent.add(Markdown(f"{subtask.title} {task_summary(subtask, today)}"))
            return tree
        else:
            # Try to find the first heading in the current tree's children
            labels = [t.label for t in tree.children]
            if task.path[0] in labels:  # The first heading has been found, continue to traverse down its children
                first_heading = task.path[0]
                task.path = task.path[1:]
                return add_to_tree(task, tree.children[labels.index(first_heading)], task_idx)
            else:  # The first heading doesn't exist, create it and traverse down its children
                child = tree.add(f"{task.path[0]}")
                task.path = task.path[1:]
                return add_to_tree(task, child, task_idx)

    for i, task in enumerate(tasks_visible):
        add_to_tree(task, tree, i)

    console.print("")
    console.print(tree)
    console.print("")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--dir', type=str, required=False,
                        help='Search for Markdown task files in this directory')
    parser.add_argument('--days', type=int, default=0,
                        help='Look ahead this number of days in the future for tasks that have reminders or are due')
    parser.add_argument('--today', type=str, required=False,
                        help='Use this date as today\'s date, e.g. --today 3/4/2022')
    parser.add_argument('task_id', type=int, nargs='?',
                        help='Show the description of this specific task')

    sys.exit(run(parser.parse_args()))
