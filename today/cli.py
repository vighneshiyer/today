import argparse
import sys
from pathlib import Path
import itertools
from datetime import date, timedelta
from typing import List

from rich import print as rprint
from rich.tree import Tree
from rich.console import Console
from rich.markdown import Markdown

from today.task import Task
from today.parser import parse_markdown
from today.output import task_should_be_displayed, task_to_string, days


def run(args) -> None:
    if args.dir:
        assert Path(args.dir).is_dir()
        root = Path(args.dir)
    else:
        root = Path.cwd()
    md_files = list(root.resolve().glob("*.md"))
    tasks_by_file: List[List[Task]] = [parse_markdown(file.read_text().split('\n')) for file in md_files]
    # Set each task's file
    for filepath, tasklist in zip(md_files, tasks_by_file):
        for task in tasklist:
            task.file_path = filepath

    # Flatten the task list
    tasks: List[Task] = list(itertools.chain(*tasks_by_file))

    # Only look at tasks that have a due/reminder date on today or number of 'days' in the future
    if args.today:
        mock_today_split = args.today.split('/')
        today = date(int(mock_today_split[2]), int(mock_today_split[0]), int(mock_today_split[1]))
    else:
        today = date.today()
    task_date_limit = today + timedelta(days=args.days)
    tasks_visible: List[Task] = [task for task in tasks if task_should_be_displayed(task, task_date_limit)]

    console = Console()

    # If a specific task id is given, print its description and details and exit
    if args.task_id is not None:
        if args.task_id < 0 or args.task_id >= len(tasks_visible):
            console.print(f"The task_id {args.task_id} does not exist")
            sys.exit(1)
        task = tasks_visible[args.task_id]
        task_title = task_to_string(task, today)
        console.print(task_title)
        task_desc = task.description
        if len(task_desc) > 0:
            md = Markdown(task_desc)
            console.print(md)
        sys.exit(0)

    # Sort tasks by their headings and due dates
    # TODO

    # Print tasks as a tree
    tree = Tree(f"Tasks for Today {today}" +
                ("" if args.days == 0 else f" (+{days(timedelta(days=args.days))})"))

    def add_to_tree(task: Task, tree: Tree, task_idx: int) -> Tree:
        if len(task.path) == 0:  # Base case
            tree.add(f"{task_idx}) {task_to_string(task, today)}")
            return tree
        else:
            # Try to find the first heading in the current tree's children
            labels = [t.label for t in tree.children]
            if task.path[0] in labels:  # The first heading has been found, continue to traverse down its children
                first_heading = task.path[0]
                task.path = task.path[1:]
                return add_to_tree(task, tree.children[labels.index(first_heading)], task_idx)
            else:  # The first heading doesn't exist, create it and traverse down its children
                child = tree.add(task.path[0])
                task.path = task.path[1:]
                return add_to_tree(task, child, task_idx)

    for i, task in enumerate(tasks):
        add_to_tree(task, tree, i)
    console.print(tree)


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
